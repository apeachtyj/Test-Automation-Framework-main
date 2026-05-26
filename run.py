import shutil
import pytest
import os
import webbrowser
import argparse

from common.semail import BuildEmail
from conf.setting import REPORT_TYPE
from common.recordlog import logs
from tools.swagger_parser import SwaggerParser
from conf.setting import REPORT_TYPE, dd_msg  # 引入钉钉开关
# 根据你的实际目录引入钉钉和邮件模块
from common.dingRobot import send_dd_msg



def sync_api_cases():
    """触发 Swagger 用例自动生成"""
    logs.info("==== 开始执行接口同步任务 ====")
    parser = SwaggerParser()
    parser.generate_yaml()


def run_tests():
    """执行自动化测试 (保留你原有的完整逻辑)"""
    logs.info(f"==== 开始执行自动化测试 (报告类型: {REPORT_TYPE}) ====")
    if REPORT_TYPE == 'allure':
        pytest.main(['-s', '-v', '--alluredir=./report/temp', './testcase', '--clean-alluredir',
                     '--junitxml=./report/results.xml'])
        try:
            shutil.copy('./environment.xml', './report/temp')
        except FileNotFoundError:
            pass
            # 2. 发送钉钉通知
        if dd_msg:
            logs.info("准备发送钉钉测试结果通知...")
            send_dd_msg("【测试通知】智慧物流系统接口自动化执行完毕，请及时查看 Allure 测试报告！")

        # 3. 发送邮件通知 (如果想发邮件，取消下方注释)
        # 注意：这里需要传入具体的成功/失败用例数。你的代码里写了 Pjenkins.py 可以解析，
        # 如果是本地跑，这里暂时传空列表演示，实际业务中可以通过 pytest hook 或解析 results.xml 获取真实数据。
        # logs.info("准备发送测试报告邮件...")
        # email = BuildEmail()
        # email.main(success=[1,2,3], failed=[], error=[], not_running=[])
        # os.system('allure serve ./report/temp')

    elif REPORT_TYPE == 'tm':
        pytest.main(['-vs', '--pytest-tmreport-name=testReport.html', '--pytest-tmreport-path=./report/tmreport'])
        webbrowser.open_new_tab(os.getcwd() + '/report/tmreport/testReport.html')


if __name__ == '__main__':
    # 使用 argparse 实现命令行调度
    cli_parser = argparse.ArgumentParser(description="接口自动化测试框架 CLI")
    cli_parser.add_argument(
        'action',
        nargs='?',
        choices=['sync', 'run', 'all'],
        default='run',
        help="执行动作: sync(仅同步生成用例), run(仅运行测试-默认), all(先同步再运行)"
    )

    args = cli_parser.parse_args()

    if args.action == 'sync':
        sync_api_cases()
    elif args.action == 'run':
        run_tests()
    elif args.action == 'all':
        sync_api_cases()
        run_tests()
        # uv run run.py run