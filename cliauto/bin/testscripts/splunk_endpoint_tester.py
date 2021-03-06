import os
import sys
import json
import logging
import time
import errno
import pdb
#pdb.set_trace()

# Setup logging
os.environ['SPLUNK_HOME'] = '/opt/splunk'
os.environ['PYTHONHTTPSVERIFY'] = '0'
logfile = os.sep.join([os.environ['SPLUNK_HOME'], 'var', 'log', 'splunk', 'cliauto.log'])
logging.basicConfig(format='%(asctime)s %(message)s', filename=logfile,level=logging.DEBUG)

# Append directory of this file to the Python path to be able to import cliauto libs
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# Import cliauto and Splunk SDK libs
from cliautolib.cliauto_endpoint import endpoint

in_string = '{"output_mode":"xml","output_mode_explicit":false,"server":{"rest_uri":"https://127.0.0.1:8089","hostname":"localhost.localdomain","servername":"localhost.localdomain","guid":"4CA6B71E-93B2-4312-B318-D354126DFFD9"},"restmap":{"name":"script:cliauto","conf":{"handler":"cliauto.cliautoHandler","match":"/cliauto","output_modes":"json","passHttpCookies":"true","passHttpHeaders":"true","passPayload":"true","requireAuthentication":"true","script":"cliauto.py","scripttype":"persist"}},"query":[],"connection":{"src_ip":"127.0.0.1","ssl":true,"listening_port":443},"session":{"user":"admin","authtoken":"fhl6W2d73DCIG7i_3n7ERnQuxq25QizYb3CyZqppAzdgyDE4WYmytk7JYvzcFmUIEYcoLKdPfuK2iwpIdDrK2yjEk^Fi0PVBzKSgXLfEPbB4WkicqchBovN8Rz^oQ47g^v2B"},"rest_path":"/cliauto","lang":"en-US","method":"POST","form":[["cmdtype","CLI"],["cmd","uptime"],["suser","root"],["spw","pass1"],["nodelist","nl1.csv"]],"headers":[["Host","127.0.0.1"],["Connection","keep-alive"],["Content-Length","65"],["Accept","text/javascript, text/html, application/xml, text/xml, */*"],["Origin","https://127.0.0.1"],["X-Requested-With","XMLHttpRequest"],["X-Splunk-Form-Key","6254940958232603202"],["User-Agent","Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"],["Content-Type","application/x-www-form-urlencoded; charset=UTF-8"],["Accept-Encoding","gzip, deflate, br"],["Accept-Language","en-US,en;q=0.9"],["Cookie","sessionid=aw59271mn1vx04x30ib8kk22ssbsm57l; csrftoken=kaf4LmlfL49Be3VBPQU07EP2JVVavTg1; mintjs%3Auuid=254efa46-8cfd-4fa3-9794-c1d61e0f1352; built_by_tabuilder=yes; ta_builder_current_ta_display_name=TestApp; ta_builder_current_ta_name=TA-testapp; splunkd_8000=2IRhsryvJ9ePTCQXLWW_GEIdGa6uiclND8^_MlDZCHWkE_eZM6VVwpbvkqe2_PFZ_QmBZBM09kezqyuW5OmmT9C1uPGGPqhPhQe7BFtfxxkqzFyNCW5_7mZOKB8G7uN04sAi; splunkweb_csrf_token_8000=12671344996474452194; session_id_8000=164024e39f347843c66cdacbc20b994a04579806; splunkd_80=lX7N6wmCxVpj05GF8ATyqBi1wmoufkObq4his8ytwBsmQwQiUZvPvUtMxX71My3QpsDKULOPIC0NCDfNwcG9^yUzyisXuE^9YiQP1eyiOKWy4Z_wFuTOTm0tz8oChkh4vE1D; splunkweb_csrf_token_80=15150253486182270537; session_id_80=391103d89f59a4db8233f296f92abead44f9e922; splunkweb_csrf_token_443=6254940958232603202; session_id_443=d63077b778a1c983fe83ac29b2fbc2599273cd12; splunkd_443=fhl6W2d73DCIG7i_3n7ERnQuxq25QizYb3CyZqppAzdgyDE4WYmytk7JYvzcFmUIEYcoLKdPfuK2iwpIdDrK2yjEk^Fi0PVBzKSgXLfEPbB4WkicqchBovN8Rz^oQ47g^v2B"]],"cookies":[["sessionid","aw59271mn1vx04x30ib8kk22ssbsm57l"],["csrftoken","kaf4LmlfL49Be3VBPQU07EP2JVVavTg1"],["mintjs%3Auuid","254efa46-8cfd-4fa3-9794-c1d61e0f1352"],["built_by_tabuilder","yes"],["ta_builder_current_ta_display_name","TestApp"],["ta_builder_current_ta_name","TA-testapp"],["splunkd_8000","2IRhsryvJ9ePTCQXLWW_GEIdGa6uiclND8^_MlDZCHWkE_eZM6VVwpbvkqe2_PFZ_QmBZBM09kezqyuW5OmmT9C1uPGGPqhPhQe7BFtfxxkqzFyNCW5_7mZOKB8G7uN04sAi"],["splunkweb_csrf_token_8000","12671344996474452194"],["session_id_8000","164024e39f347843c66cdacbc20b994a04579806"],["splunkd_80","lX7N6wmCxVpj05GF8ATyqBi1wmoufkObq4his8ytwBsmQwQiUZvPvUtMxX71My3QpsDKULOPIC0NCDfNwcG9^yUzyisXuE^9YiQP1eyiOKWy4Z_wFuTOTm0tz8oChkh4vE1D"],["splunkweb_csrf_token_80","15150253486182270537"],["session_id_80","391103d89f59a4db8233f296f92abead44f9e922"],["splunkweb_csrf_token_443","6254940958232603202"],["session_id_443","d63077b778a1c983fe83ac29b2fbc2599273cd12"],["splunkd_443","fhl6W2d73DCIG7i_3n7ERnQuxq25QizYb3CyZqppAzdgyDE4WYmytk7JYvzcFmUIEYcoLKdPfuK2iwpIdDrK2yjEk^Fi0PVBzKSgXLfEPbB4WkicqchBovN8Rz^oQ47g^v2B"]],"payload":"cmdtype=CLI&cmd=uptime&suser=root&spw=Splunk%401&nodelist=nl1.csv"}'
ep = endpoint(in_string, os.getpid())
print ep.response

