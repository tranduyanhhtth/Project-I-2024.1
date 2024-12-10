from src.crawler.products.base import BaseProduct
from src.crawler.products.power655 import ProductPower655
from src.crawler.requests.request_product import RequestPower655


class ProductMega645(ProductPower655):
    name = "mega_645"
    url = "https://vietlott.vn/ajaxpro/Vietlott.PlugIn.WebParts.Game645CompareWebPart,Vietlott.PlugIn.WebParts.ashx"

    org_body = RequestPower655(
        ORenderInfo=BaseProduct.orender_info_default,
        GameDrawId="",
        ArrayNumbers=[["" for _ in range(18)] for _ in range(6)], 
        CheckMulti=False,
        PageIndex=0,
    )