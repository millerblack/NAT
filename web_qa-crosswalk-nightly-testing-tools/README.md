Nightly Auto Test Framework
==============================
Nightly Auto Test Framework co-works with Testkit-lite tool and WRS(Web Report Service), PS(Pack package Server).


Precondition
==============================
1. Install Testkit-lite tool refer to https://github.com/testkit/testkit-lite
2. Python 2.7

To accelerate test(or save test time), some test-suites need crosswalk-test-suite, crosswalk-app-tools, you should download these repos in advance.
1.crosswalk-test-suite repo(git clone https://github.com/crosswalk-project/crosswalk-test-suite.git)
2.crosswalk-app-tools repo(git clone https://github.com/crosswalk-project/crosswalk-app-tools.git)

To test by webdriver, you need download crosswalk-web-driver repo in advance.
crosswalk-web-driver repo (git clone https://github.com/crosswalk-project/crosswalk-web-driver.git)

To configure device id list:
  Make sure configure it with sorted device ids by alpha, likes:
    sorted "id_list": ["E6OKCY410660", "E6OKCY410829", "E6OKCY410891", "E6OKCY478168"],
    not "id_list": ["E6OKCY410829", , "E6OKCY478168", "E6OKCY410660", "E6OKCY410891"],
  And according to the length of id_list, You should configure the same number test_list.spec.partx in resources/DEVICE_NAME folder (Here x in (1,2,3,4) with "id_list": ["E6OKCY410660", "E6OKCY410829", "E6OKCY410891", "E6OKCY478168"])

For webdriver test, need change group ownership & change file owner and group for /opt directory in advance:
sudo chgrp -R youraccount youraccount /opt
sudo chown -R youraccount youraccount /opt


Steps:
==============================
1. Configure 'resources/device_config.json' file
  "ASUS_MeMO_Pad_8_K011": {#device_name
    "android_version": "4.4.2",
    "device_arch": "x86",#"arm", "arm64", "x86", "x86_64"
    "device_os": "android",#"android","windows", "deepin", "ios"
    "device_type": "tablet",#"phone", "tablet"
    "wrs_branch": "stable",# when pointing one beta version as stable one, need config this key here
    "assignments": {
      "E6OKCY317686": {#device_id
        "target_binary": {
          "branch": "beta",#"master","beta"
          "mode": "embedded",#"embedded", "shared"
          "version": "latest",#"lastest",specified version
          "segment_list": ["crosswalk"]#"crosswalk","cordova4.x", "cordova3.6"
        },
        "rerun_flag": 0#0:not need to rerun,1: need to rerun
      },
      "E6OKCY410660": {
        "target_binary": {
          "branch": "beta",
          "mode": "embedded",
          "version": "latest",
          "segment_list": ["crosswalk"]
        },
        "rerun_flag": 0
      },
      "E6OKCY410891": {
        "target_binary": {
          "branch": "beta",
          "mode": "embedded",
          "version": "latest",
          "segment_list": ["crosswalk"]
        },
        "rerun_flag": 1
      }
    },
    "is_tested": 0#0-not need to test,1:need to test
  }

2. Configure 'resources/settings.json' file
  "log_level_coment": "DEBUG, INFO, WARNING, ERROR, CRITICAL",
  "log_level": "ERROR",#"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
  "env_vars": {
    "ANDROID_HOME": "/home/qawt/Tools/adt-bundle-linux-x86_64-20140702/sdk",
    "DISPLAY": ":0.0",
    "PATH": [
      "/usr/local/bin",
      "/usr/lib/jvm/jdk1.8.0_65/bin",
      "/usr/lib/jvm/jdk1.8.0_65/jre/bin",
      "/home/qawt/Tools/crosswalk-test-suite/tools/crosswalk",
      "/home/qawt/Tools/adt-bundle-linux-x86_64-20140702/sdk",
      "/home/qawt/Tools/adt-bundle-linux-x86_64-20140702/sdk/tools",
      "/home/qawt/Tools/adt-bundle-linux-x86_64-20140702/sdk/platform-tools"]
  },
  "host_infos": {
    "Host OS": "Ubuntu 12.04 LTS 64bits"
  },
  "test_env_infos": {
    "Android SDK": "Android 22",
    "Java SDK": "1.8.0_65",
    "Python": "2.7.3",
    "Testkit-lite": "3.1.16-rc1",
    "Webdriver": "v2.5.ede663c5c5362a073e538cdabacf85612bc9e16a",
    "Selenium": "2.43.0",
    "Atip": "0.0.3",
    "Behave": "1.2.4",
    "Uiautomator": "0.2.5",
    "Commit ID": "commitid"
  },
  "crosswalk_release_server_url_internal": "https://linux-ftp.sh.intel.com/pub/mirrors/01org/crosswalk/releases",
  "crosswalk_release_server_url": "https://download.01.org/crosswalk/releases",
  "package_release_server_url": "http://jiaxxx-dev.sh.intel.com/ForNightlyAutoTest",
  "crosswalk_type": "crosswalk",#"crosswalk", "crosswalk-lite"
  "test_platform": "android",#"windows", "deepin", "windows", "ios"
  "open_source_projects_dir": "/home/qawt/Tools",
  "xwalkdriver_path": "/home/qawt/Tools/crosswalk-web-driver/bin",
  "is_webdriver": 0,#0:testkit-lite tool does not run by webdriver,1:testkit-lite tool runs by webdriver
  "data_conf_platform_dic": {
    "ASUS_MeMO_Pad_8_K011": "x86-memo",
    "Google_Nexus_3": "arm-nexus3",
    "Google_Nexus_4": "arm-nexus4",
    "Google_Nexus_7": "arm-nexus7",
    "Toshiba_Excite_Go_AT7-C8": "x86-toshiba",
    "ZTE_Geek_V975": "x86-zte",
    "ECS2-8A": "x86-esc2"
  },
  "rerun_line": 30,
  "upload_type": "Nightly",
  "is_upload_report": 1,#0:not upload report files onto WRS,1:upload report files onto WRS
  "report_settings": {
    "wrs_api": "http://wrs.sh.intel.com/api",
    "authtokens": "f08b2c258bf5ec28f3f9ee06fced741eb9b6f760"#get this authtokens after you sign in WRS
  },
  "mail_settings": {
    "mail_object": "Milestone Full Auto Test",
    "mail_list": [
      "fengx.dai@intel.com",
      "xiaoyux.zhang@intel.com",
      "yunfeix.hao@intel.com",
      "xiuqix.jiang@intel.com",
      "canx.cao@intel.com",
      "xiaolongx.xie@intel.com",
      "wenhaox.jiang@intel.com",
      "weiweix.li@intel.com"],
    "mail_cclist": [
      "yugang.fan@intel.com"],
    "mail_bcclist": [],
    "mail_host": "smtp.intel.com:25",
    "mail_user": "fengx.dai",
    "mail_postfix": "intel.com"
  }

3.Assign test suite list for device
  create device_name directory in resouces # 'device_name' should be the same as you configured in resource
    mkdir resouces/device_name

  if you assign the only one device of device_name, you should create test_list.spec in you just created device_name directory,
  otherwise, you assign two (or n which more than two) devices of this device_name, you should create test_list.spec.part1, test_list.spec.part2(..., test_list.spec.partn) in just created device_name directory,
  in test_list.spec or test_list.spec.partn file(s) in resouces/device_name, you need add test suite name likes:
    tct-sse-w3c-tests
    tct-svg-html5-tests
    tct-text-css3-tests
    tct-touchevent-w3c-tests
    tct-transitions-css3-tests
    tct-typedarrays-nonw3c-tests
    tct-ui-css3-tests


Accessories tools
==============================
A1. ntreport tool: upload test resutl xml/csv files onto WRS
A1.1.1 Config 'upload_config.json'
  For easily manual-upload result xml/csv files, you can refer to 'resources/device_config.json' and quick config 'upload_config.json' in the result directory, and the content of 'upload_config.json' likes following:
  {
      "xw_type": "crosswalk-lite",#"crosswalk", "crosswalk-lite"
      "platform": "android",#"android","windows", "deepin", "ios"
      "android_version": "4.4.2",
      "segment": "crosswalk",#"crosswalk","cordova4.x", "cordova3.6"
      "binary_branch": "master",#"master","beta", "stable"
      "binary_version": "18.46.471.0",
      "device_name": "ASUS_MeMO_Pad_8_K011",
      "device_arch": "x86",#"arm", "arm64", "x86", "x86_64"
      "device_type": "tablet",#"phone", "tablet"
      "mode": "embedded",#"embedded","shared"
      "commit_id": "id value", #set id value
      "upload_type": "Nigthly"
  }
A1.1.2 Upload result xml files
    $cd scripts/util
    $python ntreport.py <dst_dir>
A1.1.3 Upload result csv files
  Create template csv directories, execute
    $cd scripts/util
    $python create_csv_template_dirs.py <dst_dir>
  then prepare the result csv files into correspondent directories of <dst_dir>,
  modify the content of 'upload_config.json' in <dst_dir> following above A1.1.1
  upload result csv files, execute the commands:
    $cd scripts/util
    $python ntreport_csv.py <dst_dir>

A1.2 If <dst_dir> was generated by Nightly Auto Test Framework, don't need to config 'upload_config.json' in the <dst_dir>, execute the same commands of A1.1.2 .
