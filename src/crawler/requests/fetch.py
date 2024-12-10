import re 
from typing import Callable, Optional, Tuple

import requests
from loguru import logger

from src.crawler.requests.config_header import TIMEOUT


def get_vietlott_cookie() -> Tuple[str, dict]:
    res = requests.get("https://vietlott.vn/ajaxpro/")
    match = re.search(r'document.cookie="(.*?)"', res.text)
    if match is None:
        raise ValueError(f"cookie is None, text={res.text}")
    cookie = match.group(1)
    cookies = {cookie.split("=")[0]: cookie.split("=")[1]}
    return cookie, cookies


def fetch_wrapper( 
    url: str, 
    headers: Optional[dict], 
    org_params: Optional[dict], 
    org_body: dict, 
    process_result_fn: Callable, 
    cookies: Optional[dict] ):
    """
    Trả về một hàm con (fetch) lấy dữ liệu cho một tập hợp các params(tham số) và body(dữ liệu)
    fetch() gửi các yêu cầu HTTP POST đến một URL với các params và body được cung cấp và xử lý kết quả của các yêu cầu đó
    """
    def fetch(tasks):
        """
        1. Thực hiện lấy dữ liệu trên nhiều yêu cầu
        2. - Ghi lại các ID của các tác vụ (tasks) được xử lý
           - Tạo một bản sao của headers để tránh thay đổi trực tiếp headers gốc
        3. - Lặp qua các tác vụ (tasks), sao chép để tạo các params và body riêng cho từng yêu cầu
           - Cập nhật params và body với thông tin từ task hiện tại
           - Gửi yêu cầu POST đến URL với params và body được cập nhật
          + Nếu yêu cầu không thành công, ghi lại lỗi và tiếp tục với tác vụ tiếp theo.
          + Nếu yêu cầu thành công, xử lý kết quả (process_result_fn) và thêm kết quả vào danh sách kết quả
           - Ghi lại thông báo task done khi tác vụ hoàn thành, trả về mảng results
        """
        tasks_str = ",".join(str(t["task_id"]) for t in tasks)
        logger.debug(f"worker start, tasks_ids={tasks_str}")
        _headers = headers.copy()

        results = []
        for task in tasks:
            task_id, task_data = task["task_id"], task["task_data"]
            params = org_params.copy()
            body = org_body.copy()

            params.update(task_data["params"])
            body.update(task_data["body"])

            res = requests.post(
                url,
                json=body,
                params=params,
                headers=_headers,
                cookies=cookies,
                timeout=TIMEOUT,
            )

            if not res.ok:
                logger.error(
                    f"req fail, args={task_data}, code={res.status_code}, text={res.text[:200]}, headers={_headers}, body={body}, params={params}"
                )
                continue
            try:
                result = process_result_fn(params, body, res.json(), task_data)
                results.append(result)
                logger.debug(f"task {task_id} done")
            except requests.exceptions.JSONDecodeError as e:
                logger.error(
                    f"json decode error, args={task_data}, text={res.text[:200]}, headers={headers}, cookies={cookies}, body={body}, params={params}"
                )
                raise e
        logger.debug(f"worker done, tasks={tasks_str}")
        return results

    return fetch
