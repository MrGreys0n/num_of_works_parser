import fake_useragent
import os
import re
import requests
import gspread

from bs4 import BeautifulSoup, element
from datetime import datetime, timedelta
from pathlib import Path


class Parser:
    def __init__(self) -> None:
        self.session: requests.Session = requests.Session()
        self.login_data: dict[str, str] = {"email": os.getenv("EMAIL"), "password": os.getenv("PASSWORD")}
        self.headers: dict[str, str] = {"user-agent": fake_useragent.UserAgent().random}

        self.checks: dict[str, int] = dict()

        self.gc: gspread.Client = gspread.service_account(filename=Path(__file__).parent.resolve() / "credentials.json")
        self.wks: gspread.Worksheet = self.gc.open("Цепной пёс проверки").sheet1

        if datetime.now().hour < 1:
            self.date: str = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
        else:
            self.date: str = (datetime.now()).strftime("%d.%m.%Y")
        self.__login()

    def __login(self) -> None:
        self.session.post(
            url=os.getenv("LOGIN_URL"),
            data=self.login_data,
            headers=self.headers
        )

    def execute(self) -> None:
        self.__get_logins_from_sheet()
        self.__parse_stats()
        self.__update_table()

    def __get_logins_from_sheet(self) -> None:
        logins_from_wks: list[list[str]] = self.wks.get_values("C3:C")
        for login_from_wks in logins_from_wks:
            self.checks[login_from_wks[0].strip()] = 0

    def __parse_stats(self) -> None:
        url: str = (os.getenv("CHECKS_URL")
                    .replace("DATE", self.date)
                    .replace("PAGE_NO", "1"))

        soup: BeautifulSoup = self.__get_soup(url)
        num_of_pages: int = self.__get_num_of_pages(soup)

        for i in range(1, num_of_pages + 1):
            if i > 1:
                url: str = (os.getenv("CHECKS_URL")
                            .replace("DATE", self.date)
                            .replace("PAGE_NO", str(i)))
                soup: BeautifulSoup = self.__get_soup(url)

            rows: list[element] = soup.find_all("tr", class_="odd")
            for row in rows:
                cells: list[element] = row.find_all("td")
                login: str = cells[2].get_text(strip=True)
                if login in self.checks.keys():
                    checked: int = int(cells[4].get_text(strip=True)) + int(cells[6].get_text(strip=True))
                    self.checks[login] = checked

    def __update_table(self) -> None:
        list_of_checks: list[int] = list(self.checks.values())
        list_for_sheet: list[list[int]] = [[el] for el in list_of_checks]

        cell: gspread.Cell | None = self.wks.find(self.date)
        self.wks.update(f"R{cell.row + 1}C{cell.col}:R{cell.row + len(self.checks)}C{cell.col}", list_for_sheet)

    def __get_soup(self, url: str) -> BeautifulSoup:
        url_response = self.session.get(url, headers=self.headers).text
        return BeautifulSoup(url_response, "html.parser")

    @staticmethod
    def __get_num_of_pages(soup: BeautifulSoup) -> int:
        div = soup.find("div", id="example2_info")
        if div is None:
            return 1
        return int(re.findall(r"\d+", div.text)[-1]) // 15 + 1
