import click
import pendulum

from src.crawler.config.map_class import map_class_name
from src.crawler.config.products import product_config_map
from src.crawler.products.base import BaseProduct


@click.command()
@click.pass_context
@click.argument("product")
@click.option("--run-date", default=pendulum.now(tz="Asia/Ho_Chi_Minh").to_date_string(), help="Ngày lấy dữ liệu (default : ngày hiện tại ở múi giờ Việt Nam)")
@click.option("--index_from", default=0, type=int, help="index_page from : trang mới nhất")
@click.option("--index_to", default=None, type=int, help="index_page to: trang cũ hơn")
def crawl(ctx, product, run_date, index_from, index_to):
    """
    Lấy dữ liệu sản phẩm có trong bảng map
    """
    if product not in product_config_map:
        click.echo(f"Error:: Product must in product_map: {list(product_config_map.keys())}", err=True)
        ctx.exit(1)
    click.echo(f"product={product}")

    product_obj: BaseProduct = map_class_name[product]()
    product_obj.crawl(
        run_date_str=run_date,
        index_from=index_from,
        index_to=index_to,
    )


if __name__ == "__main__":
    crawl()
