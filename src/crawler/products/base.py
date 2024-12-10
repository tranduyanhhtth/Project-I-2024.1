from src.crawler.config.products import get_config
from src.crawler.requests import config_header as requests_config
from src.crawler.requests.fetch import get_vietlott_cookie
from src.crawler.requests.request_product import ORenderInfoCls


class BaseProduct:
    name = ""
    url = ""
    page_to_run: int = 1
    stored_data_dtype = {}

    org_body = None
    org_params = None

    product_config = None

    orender_info_default = ORenderInfoCls(
        SiteId="main.frontend.vi",
        SiteAlias="main.vi",
        UserSessionId="",
        SiteLang="vi",
        IsPageDesign=False,
        ExtraParam1="",
        ExtraParam2="",
        ExtraParam3="",
        SiteURL="",
        WebPage=None,
        SiteName="Vietlott",
        OrgPageAlias=None,
        PageAlias=None,
        RefKey=None,
        FullPageAlias=None,
    )

    def __init__(self):
        self.product_config = get_config(self.name)
        self.headers = requests_config.headers

        if self.product_config.use_cookies:
            self.vietlott_cookie, self.cookies = get_vietlott_cookie()
            self.headers.update({"Cookie": self.vietlott_cookie})
        else:
            self.vietlott_cookie, self.cookies = None, None

    def process_result(self, params, body, res_json, task_data):
        pass

    def crawl(self, run_date_str, index_from, index_to):
        pass
