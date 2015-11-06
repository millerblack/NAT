#!/bin/bash
result_path=$1
wttestsxml_path=$2
webdriver_mode=$3
pwd=$PWD
cd ${result_path}
result_save_path=${result_path}
result_file=${result_path}/../analyzed_result.txt
attach_file=${result_path}/../report_details.html
compare_flag=0
last_report_path=${result_path}/../../last_report
if [ -d ${last_report_path} ];then
    if [ -e ${last_report_path}/report_details.html ];then
        compare_flag=1
    fi
else
    mkdir ${last_report_path}
fi

#compare with last has no sense
compare_flag=0

function get_percent(){
  rate_percent=`python $pwd/get_percent.py $1 $2`
  echo $rate_percent
}


function adjust(){
  l=`grep -rn 'execution_type="auto"' $1 | grep 'subcase=' | awk -F 'subcase="' {'print $2'} | cut -d '"' -f1`
  subcase_total_num=0

  for i in $l
  do
    let subcase_total_num=subcase_total_num+i
  done

  double_count_num=0
  l1=`grep -rn 'execution_type="auto"' $1 | grep 'subcase=' | cut -d ':' -f1 | uniq`
  for xml_file in $l1
  do
    case_num=`grep -rn 'execution_type="auto"' ${xml_file} | wc -l`
    let double_count_num=double_count_num+case_num
  done
  let adjust_tcs_num=subcase_total_num-double_count_num
  echo $adjust_tcs_num
}


function adjust_total_tcs(){
  adjust_tcs_num=$(adjust $2)
  let adjusted_total_tcs=$1+$adjust_tcs_num
  echo $adjusted_total_tcs
}


function get_summary_data(){
  testsxml_dir=$1
  #result_dir=$2
  #total_tcs=`grep -rn 'execution_type="auto"' ${testsxml_dir} | wc -l`
  #total_tcs=$(adjust_total_tcs $total_tcs ${testsxml_dir})
  pass_num=0
  fail_num=0

  if [ $webdriver_mode -eq 1 ];then
    total_tcs=`grep -Ern 'execution_type="auto"|execution_type="manual"' ${testsxml_dir} | wc -l`
  else
    total_tcs=`grep -rn 'execution_type="auto"' ${testsxml_dir} | wc -l`
  fi
  
  total_tcs=$(adjust_total_tcs $total_tcs ${testsxml_dir})

  for test_set in `ls $result_save_path`
  do
    for res_file in `ls $result_save_path/$test_set`
    do
      result=`python $pwd/analyze_results_special.py $result_save_path/$test_set/$res_file`
      sub_total=`echo $result | cut -d ' ' -f1`
      sub_pass=`echo $result | cut -d ' ' -f2`
      sub_fail=`echo $result | cut -d ' ' -f3`
      sub_block=`echo $result | cut -d ' ' -f4`
      let pass_num=pass_num+sub_pass
      let fail_num=fail_num+sub_fail
    done
  done
     
  let block_num=total_tcs-pass_num-fail_num
  let total_run=total_tcs-block_num
  run_rate_percent=$(get_percent $total_run $total_tcs)%
  pass_rate_percent=$(get_percent $pass_num $total_tcs)%
  echo "Total TCs:" $total_tcs ", Passed:" $pass_num ", Failed:" $fail_num ", Blocked:" $block_num ", Run%:" $run_rate_percent ", Pass%:" $pass_rate_percent >>${result_file}
  echo >>${result_file}
}

function get_data(){
  #total_tcs=`grep -rn 'execution_type="auto"' ${wttestsxml_path}/$1 | wc -l`

  if [ $webdriver_mode -eq 1 ];then
    total_tcs=`grep -Ern 'execution_type="auto"|execution_type="manual"' ${testsxml_dir} | wc -l`
  else
    total_tcs=`grep -rn 'execution_type="auto"' ${testsxml_dir} | wc -l`
  fi

  total_tcs=$(adjust_total_tcs $total_tcs ${wttestsxml_path}/$1)
  pass_num=0
  fail_num=0

  for res_file in `ls $result_save_path/$1`
  do
    result=`python $pwd/analyze_results_special.py $result_save_path/$1/$res_file`
    sub_total=`echo $result | cut -d ' ' -f1`
    sub_pass=`echo $result | cut -d ' ' -f2`
    sub_fail=`echo $result | cut -d ' ' -f3`
    sub_block=`echo $result | cut -d ' ' -f4`
    let pass_num=pass_num+sub_pass
    let fail_num=fail_num+sub_fail
  done
  
  let block_num=total_tcs-pass_num-fail_num
  let total_run=total_tcs-block_num
  run_rate_percent=$(get_percent $total_run $total_tcs)%
  pass_rate_percent=$(get_percent $pass_num $total_tcs)%
  test_set=$1
  test_set=`echo $1 | sed -e "s/API/ API/"`
  echo "------------" $test_set "------------" >>${result_file}
  echo "Total TCs:" $total_tcs ", Passed:" $pass_num ", Failed:" $fail_num ", Blocked:" $block_num ", Run%:" $run_rate_percent ", Pass%:" $pass_rate_percent >>${result_file}
}

find ${result_path} -name '*.dmesg' -delete
find ${result_path} -name '*.logcat' -delete
get_summary_data ${wttestsxml_path}

for test_set in `ls $result_save_path ` 
do
  get_data $test_set
done

#generate report_details.html
function get_pass_rate_td(){
    pass_rate=$1
    if [ $pass_rate -ge 90 ];then
      echo "                <td><font color="green">$pass_rate%</font></td>" >> $attach_file
    elif [ $pass_rate -ge 30 ];then
      echo "                <td><font color="orange">$pass_rate%</font></td>" >> $attach_file
    elif [ $pass_rate -ge 0 ];then
      echo "                <td><font color="red">$pass_rate%</font></td>" >> $attach_file
    fi
}

function get_compare_tds(){
   last_pass_rate_td=`grep $1 -A5 ${last_report_path}/report_details.html | grep '%'`
   if [ -n "$last_pass_rate_td" ];then
       echo $last_pass_rate_td  >> $attach_file
       last_pass_rate=`echo $last_pass_rate_td | cut -d '%' -f1 | cut -d '>' -f3`
       if [ "$2" -gt "$last_pass_rate" ];then
           echo "                <td><font color="green">↑</font></td>" >> $attach_file
       elif [ "$2" -lt "$last_pass_rate" ];then
           echo "                <td><font color="red">↓</font></td>" >> $attach_file
       else
           echo "                <td>-</td>" >> $attach_file
       fi
   else
       echo "                <td>N/A</td>" >> $attach_file
       echo "                <td><font color="green">↑</font></td>" >> $attach_file
   fi
}


echo "<html>" >> $attach_file
echo "<head>" >> $attach_file
echo '<meta http-equiv="Content-Type" content="text/html; charset=gb2312" />' >> $attach_file
echo '<style type="text/css">' >> $attach_file
echo "#customers" >> $attach_file
echo "  {" >> $attach_file
echo '  font-family:"Trebuchet MS", Arial, Helvetica, sans-serif;' >> $attach_file
echo '  width:100%;' >> $attach_file
echo '  border-collapse:collapse;' >> $attach_file
echo "  }" >> $attach_file
echo '#customers td, #customers th' >> $attach_file
echo "  {" >> $attach_file
echo "  font-size:1em;" >> $attach_file
echo "  border:1px solid #e0e0e0;" >> $attach_file
echo "  padding:3px 7px 2px 7px;" >> $attach_file
echo "  }" >> $attach_file
echo "#customers th" >> $attach_file
echo "  {" >> $attach_file
echo "  font-size:14;" >> $attach_file
echo "  text-align:left;" >> $attach_file
echo "  padding-top:5px;" >> $attach_file
echo "  padding-bottom:4px;" >> $attach_file
echo "  background-color:#a2a2a2;" >> $attach_file
echo "  color:black;" >> $attach_file
echo "  }" >> $attach_file
echo "#customers tr.alt td" >> $attach_file
echo "  {" >> $attach_file
echo "  background-color:#f2f2f2;" >> $attach_file
echo "  }" >> $attach_file
echo "</style>" >> $attach_file
echo "</head>" >> $attach_file
echo "    <body>" >> $attach_file
echo '        <table id="customers">' >> $attach_file
echo "            <tr>" >> $attach_file
echo "                <th>Web Spec</th>" >> $attach_file
echo "                <th>Total TCs</th>" >> $attach_file
echo "                <th>Passed</th>" >> $attach_file
echo "                <th>Failed</th>" >> $attach_file
echo "                <th>Blocked</th>" >> $attach_file
echo "                <th>Pass%</th>" >> $attach_file
if [ $compare_flag -eq 1 ];then
    echo "                <th>Last Pass%</th>" >> $attach_file
    echo "                <th>Tend</th>" >> $attach_file
fi
echo "            </tr>" >> $attach_file
color_flag=0
for test_set in `ls $result_save_path | grep -v Feature`
do
  for f in `ls $result_save_path/$test_set`
  do
    res_file=$result_save_path/$test_set/$f
    suite_name=`grep '<suite' $res_file | awk -F ' name="' '{print $2}' | cut -d '"' -f1 | sed -e 's/tct-//'`
    result=`python $pwd/analyze_results_special.py $res_file`
    total=`echo $result | cut -d ' ' -f1`
    passed=`echo $result | cut -d ' ' -f2`
    failed=`echo $result | cut -d ' ' -f3`
    blocked=`echo $result | cut -d ' ' -f4`
    pass_rate=$(get_percent $passed $total)

    if [ $color_flag -eq 1 ];then
      echo '            <tr class="alt">' >> $attach_file
      let color_flag=0
    else
      echo '            <tr>' >> $attach_file
      let color_flag=1
    fi
    echo "                <td>$suite_name</td>" >> $attach_file
    echo "                <td>$total</td>" >> $attach_file
    echo "                <td><font color="green">${passed}</font></td>" >> $attach_file
    echo "                <td><font color="red">${failed}</font></td>" >> $attach_file
    echo "                <td>$blocked</td>" >> $attach_file
    get_pass_rate_td $pass_rate
    if [ $compare_flag -eq 1 ];then
        get_compare_tds $suite_name $pass_rate
    fi
    echo "            </tr>" >> $attach_file
  done
done
echo '        </table>' >> $attach_file

feature_flag=`ls $result_save_path | grep Feature | wc -l`
if [ $feature_flag -eq 1 ]; then
echo "<br>" >> $attach_file
echo "<br>" >> $attach_file
echo '        <table id="customers">' >> $attach_file
echo "            <tr>" >> $attach_file
echo "                <th>Component</th>" >> $attach_file
echo "                <th>Total TCs</th>" >> $attach_file
echo "                <th>Passed</th>" >> $attach_file
echo "                <th>Failed</th>" >> $attach_file
echo "                <th>Blocked</th>" >> $attach_file
echo "                <th>Pass%</th>" >> $attach_file
if [ $compare_flag -eq 1 ];then
    echo "                <th>Last Pass%</th>" >> $attach_file
    echo "                <th>Tend</th>" >> $attach_file
fi
echo "            </tr>" >> $attach_file

let color_flag=0

for test_set in `ls $result_save_path | grep Feature`
do
  for f in `ls $result_save_path/$test_set`
  do
    res_file=$result_save_path/$test_set/$f
    suite_name=`grep '<suite' $res_file | awk -F ' name="' '{print $2}' | cut -d '"' -f1`
    result=`python $pwd/analyze_results_special.py $res_file`
    total=`echo $result | cut -d ' ' -f1`
    passed=`echo $result | cut -d ' ' -f2`
    failed=`echo $result | cut -d ' ' -f3`
    blocked=`echo $result | cut -d ' ' -f4`
    pass_rate=$(get_percent $passed $total)
    if [ $color_flag -eq 1 ];then
      echo '            <tr class="alt">' >> $attach_file
      let color_flag=0
    else
      echo '            <tr>' >> $attach_file
      let color_flag=1
    fi

    echo "                <td>$suite_name</td>" >> $attach_file
    echo "                <td>$total</td>" >> $attach_file
    echo "                <td><font color="green">$passed</font></td>" >> $attach_file
    echo "                <td><font color="red">$failed</font></td>" >> $attach_file
    echo "                <td>$blocked</td>" >> $attach_file
    get_pass_rate_td $pass_rate
    if [ $compare_flag -eq 1 ];then
        get_compare_tds $suite_name $pass_rate
    fi
    echo "            </tr>" >> $attach_file
  done
done
echo '        </table>' >> $attach_file
fi
echo "    </body>" >> $attach_file
echo "</html>" >> $attach_file

attach_windows_file=${result_path}/../report_details_windows.html
iconv ${attach_file} -f utf8 -t gbk > ${attach_windows_file}
mv ${attach_windows_file} ${attach_file}
mv ${result_file} ${result_path}
cp ${attach_file} $last_report_path
mv ${attach_file} ${result_path}
#rm -r ${wttestsxml_path}
