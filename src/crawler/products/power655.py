import math
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Optional, List, Dict

import cattrs
import itertools
import pandas as pd
from bs4 import BeautifulSoup
from loguru import logger

from src.crawler.requests import config_header as requests_config
from src.crawler.config.products import ProductConfig
from src.crawler.products.base import BaseProduct
from src.crawler.requests import fetch
from src.crawler.requests.request_product import RequestPower655


class ProductPower655(BaseProduct):
    name = "power_655"
    url = "https://vietlott.vn/ajaxpro/Vietlott.PlugIn.WebParts.Game655CompareWebPart,Vietlott.PlugIn.WebParts.ashx"
    page_to_run = 1  # roll every 2 days

    stored_data_dtype = {
        "date": str,
        "id": str,
        "result": "list",
        "page": int,
        "process_time": str,
    }

    org_body = RequestPower655(
        ORenderInfo=BaseProduct.orender_info_default,
        GameDrawId="",
        ArrayNumbers=[["" for _ in range(18)] for _ in range(5)],
        CheckMulti=False,
        PageIndex=0,
    )
    org_params = {}

    product_config: Optional[ProductConfig] = None

    def __init__(self):
        super(ProductPower655, self).__init__()

    def process_result(self, params, body, res_json, task_data) -> List[Dict]:
        """
        Xử lý kết quả mega 6/45 và power 6/55
        Trả về List kiểu dictionary : data {date, id, result, page, process_time}
        """
        soup = BeautifulSoup(res_json.get("value", {}).get("HtmlContent"), "lxml")
        data = []
        for i, tr in enumerate(soup.select("table tr")):
            if i == 0:
                continue
            tds = tr.find_all("td")
            row = {}

            row["date"] = datetime.strptime(tds[0].text, "%d/%m/%Y").strftime("%Y-%m-%d")
            row["id"] = tds[1].text

            # last number of special
            row["result"] = [int(span.text) for span in tds[2].find_all("span") if span.text.strip() != "|"]
            row["page"] = body.get("PageIndex", -1)
            row["process_time"] = datetime.now().isoformat()

            data.append(row)
        return data

    @staticmethod
    def split_data(data, n):
        it = iter(data)
        while True:
            _data = tuple(itertools.islice(it, n))
            if not _data:
                return
            yield _data

    def crawl(self, run_date_str: str, index_from: int = 0, index_to: int = 1):
        """
        Lấy dữ liệu từ nhiều (m) luồng với ThreadPoolExecutor
        Mỗi luồng sẽ lấy dữ liệu từ n trang (n = tổng số trang / m)

        crawl [index_from, index_to]
        :param product_config:
        :param index_from: trang bắt đầu, default = 0 (1 page)
        :param index_to: trang kêt thúc, default = 1 (1 page)
        """
        if index_to is None:
            index_to = self.product_config.default_index_to

        if index_to == index_from:
            index_to += 1

        pool = ThreadPoolExecutor(self.product_config.num_thread)
        page_per_task = math.ceil((index_to - index_from) / self.product_config.num_thread)
        tasks = self.split_data(
            [
                {
                    "task_id": i,
                    "task_data": {
                        "params": {},
                        "body": {"PageIndex": i},
                        "run_date_str": run_date_str,
                    },
                }
                for i in range(index_from, index_to + 1)
            ],
            page_per_task,
        )

        logger.info(
            f"there are {index_to - index_from} pages, from {index_from}->{index_to}, {page_per_task} page per task"
        )
        fetch_fn = fetch.fetch_wrapper(
            self.url,
            requests_config.headers,
            self.org_params,
            cattrs.unstructure(self.org_body),
            self.process_result,
            self.cookies,
        )

        results = pool.map(fetch_fn, tasks)

        # Nhóm dữ liệu theo ngày 
        date_dict = defaultdict(list)
        for date_x in results:
            for date_y in date_x:
                for row in date_y:
                    date_dict[row["date"]].append(row)

        list_data = []
        for date, date_items in date_dict.items():
            list_data += date_items
        if len(list_data) == 0:
            logger.info("No results")
            return
        df_crawled = pd.DataFrame(list_data)
        logger.info(
            f'crawled data date: min={df_crawled["date"].min()}, max={df_crawled["date"].max()}'
            + f' id min={df_crawled["id"].min()}, max={df_crawled["id"].max()}'
            + f", records={len(df_crawled)}"
        )

        # Lưu dữ liệu
        current_data_count = 0
        if self.product_config.raw_path.exists():
            current_data = pd.read_json(self.product_config.raw_path, lines=True, dtype=self.stored_data_dtype)
            logger.info(
                f'current data date min={current_data["date"].min()}, max={current_data["date"].max()}'
                + f' id min={current_data["id"].min()}, max={current_data["id"].max()}'
                + f", records={len(current_data)}"
            )
            current_data_count = len(current_data)
            df_take = df_crawled[~df_crawled["id"].isin(current_data["id"])]
            df_final = pd.concat([current_data, df_take], axis="rows")
        else:
            df_final = df_crawled
        df_final = df_final.sort_values(by=["date", "id"])

        logger.info(
            f'final data min_date={df_final["date"].min()}, max_date={df_final["date"].max()}'
            + f", records={current_data_count}->{len(df_final)}, diff:{len(df_final) - current_data_count}"
        )
        df_final.to_json(self.product_config.raw_path.absolute(), orient="records", lines=True)

        logger.info(f"wrote to file {self.product_config.raw_path.absolute()}")
