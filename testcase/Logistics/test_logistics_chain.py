import allure
import pytest

from base.apiutil_business import RequestBase
from base.generateId import c_id, m_id
from common.readyaml import get_testcase_yaml


@allure.feature(next(m_id) + "Smart logistics full-chain")
class TestLogisticsChain:

    @allure.story(next(c_id) + "Order-dispatch-execution-settlement")
    @pytest.mark.parametrize("case_info", get_testcase_yaml("./testcase/Logistics/logistics_chain.yml"))
    def test_logistics_full_chain(self, case_info):
        allure.dynamic.title(case_info["baseInfo"]["api_name"])
        RequestBase().specification_yaml(case_info)
