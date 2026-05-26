import re
import sys
import time
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory, session

FRONTEND_DIR = Path(__file__).resolve().parent
BASE_DIR = FRONTEND_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from conf.operationConfig import OperationConfig  # noqa: E402

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
app.secret_key = "logistics-test-platform-dev-secret"

USERS = {
    "admin": {
        "password": "123456",
        "role": "测试管理员",
    }
}

JOBS = {}


def login_required(handler):
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return jsonify({"message": "未登录"}), 401
        return handler(*args, **kwargs)

    wrapper.__name__ = handler.__name__
    return wrapper


def count_files(relative_dir, patterns):
    target = BASE_DIR / relative_dir
    if not target.exists():
        return 0
    return sum(1 for pattern in patterns for _ in target.rglob(pattern))


def mock_routes():
    mock_file = BASE_DIR / "mock_server" / "api_server" / "base" / "flask_service.py"
    if not mock_file.exists():
        return []

    content = mock_file.read_text(encoding="utf-8", errors="ignore")
    routes = re.findall(r"@api\.route\('([^']+)'", content)
    return routes


def build_job():
    job_id = uuid4().hex[:10]
    JOBS[job_id] = {
        "job_id": job_id,
        "created_at": time.time(),
        "status": "running",
        "logs": [
            "[start] uv run python -m pytest testcase/Logistics/test_logistics_chain.py -s",
            "[auth] session user verified",
        ],
    }
    return JOBS[job_id]


def refresh_job(job):
    steps = [
        "[case] Create order plan -> passed",
        "[context] orderNo saved to GlobalContext",
        "[case] Master receives order -> passed",
        "[case] Assign carrier -> passed",
        "[case] Carrier receives order -> passed",
        "[context] logisticsOrderId saved to GlobalContext",
        "[case] Split logistics order -> passed",
        "[case] Dispatch vehicle -> passed",
        "[context] scheduleNo saved to GlobalContext",
        "[case] Inventory outbound callback -> passed",
        "[case] Measurement return -> passed",
        "[case] Create settlement bill -> passed",
        "[case] Query payable cost -> passed",
        "[done] full-chain test passed",
    ]
    elapsed = int(time.time() - job["created_at"])
    visible = min(len(steps), elapsed + 1)
    job["logs"] = job["logs"][:2] + steps[:visible]
    if visible == len(steps):
        job["status"] = "passed"
    return job


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")
    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"message": "用户名或密码错误"}), 401

    session["user"] = {"username": username, "role": user["role"]}
    return jsonify({"user": session["user"]})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "ok"})


@app.route("/api/me")
@login_required
def me():
    return jsonify({"user": session["user"]})


@app.route("/api/dashboard")
@login_required
def dashboard():
    conf = OperationConfig()
    routes = mock_routes()
    case_files = count_files("testcase", ["*.yml", "*.yaml"])
    flow = [
        {"name": "创建订单", "status": "done"},
        {"name": "集团接单", "status": "done"},
        {"name": "分配承运商", "status": "done"},
        {"name": "调度派车", "status": "running"},
        {"name": "执行回写", "status": ""},
        {"name": "结算对账", "status": ""},
    ]
    return jsonify({
        "environment": f"本地环境 {conf.get_section_for_data('api_envi', 'host')}",
        "metrics": {
            "chain_nodes": 12,
            "mock_routes": len(routes),
            "case_files": case_files,
            "report_type": conf.get_report_type("type") or "allure",
        },
        "flow": flow,
    })


@app.route("/api/cases")
@login_required
def cases():
    rows = [
        {
            "path": "testcase/Logistics",
            "type": "全链路",
            "count": count_files("testcase/Logistics", ["*.yml", "*.yaml", "*.py"]),
            "status": "ready",
            "label": "已接入",
        },
        {
            "path": "testcase/ProductManager",
            "type": "单接口",
            "count": count_files("testcase/ProductManager", ["*.yml", "*.yaml", "*.py"]),
            "status": "ready",
            "label": "可运行",
        },
        {
            "path": "testcase/AutoGenerate",
            "type": "Swagger",
            "count": count_files("testcase/AutoGenerate", ["*.yml", "*.yaml"]),
            "status": "warn",
            "label": "可同步",
        },
    ]
    return jsonify({"cases": rows})


@app.route("/api/mock")
@login_required
def mock():
    routes = mock_routes()
    featured = [
        ("/dar/user/login", "登录与 Cookie/JWT"),
        ("/api/order/customer/orderPlan/create", "货主下单"),
        ("/api/order/pc/logisticsOrder/handCapacityDispatch", "调度派车"),
        ("/rpc/srm/inventory", "仓储出库回写"),
        ("/order/feign/dbjlxt", "计量系统回传"),
        ("/api/order/pc/cost/payCost/page", "应付费用查询"),
    ]
    endpoints = [{"path": path, "desc": desc} for path, desc in featured if path in routes]
    return jsonify({"total": len(routes), "endpoints": endpoints})


@app.route("/api/ci")
@login_required
def ci():
    conf = OperationConfig()
    return jsonify({
        "job_name": conf.get_section_jenkins("job_name") or "logistics-api-test",
        "install": "uv sync",
        "test": "uv run python run.py run",
        "artifacts": "report/results.xml, report/temp, logs/**",
    })


@app.route("/api/run-tests", methods=["POST"])
@login_required
def run_tests():
    return jsonify(build_job())


@app.route("/api/jobs/<job_id>")
@login_required
def job_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"message": "任务不存在"}), 404
    return jsonify(refresh_job(job))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9000, debug=False)
