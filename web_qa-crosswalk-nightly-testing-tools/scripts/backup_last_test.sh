device_name=$1
last_test_date=$2
mv ../repo/crosswalk/iot/master/latest ../repo/crosswalk/iot/master/"$last_test_date"
mv ../test-result/crosswalk/iot/crosswalk/master/"$device_name"/embedded/latest ../test-result/crosswalk/iot/crosswalk/master/"$device_name"/embedded/"$last_test_date" 
