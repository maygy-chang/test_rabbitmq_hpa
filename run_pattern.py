import os
from define import pattern_path, traffic_pattern


def input_pattern():
    file_list = os.listdir(pattern_path)
    print "Find %s tracefiles in %s\n" % (len(file_list), pattern_path)
    print "List tracefiles"
    print "- %s\n" % (",".join(file_list))
    default_tracefile = "transaction.txt.alibaba2017-144"
    new_tracefile = raw_input("Input Pattern(default:transaction.txt.alibaba2017-144): ")
    if new_tracefile:
        is_find = False
        for file_name in file_list:
            if file_name.find(new_tracefile) != -1:
                is_find = True
                default_tracefile = file_name
                break
        if new_tracefile and not is_find:
            raise Exception("Input speficif correct traffic pattern!")
        default_tracefile = new_tracefile
    return default_tracefile


def replace_transaction(new_tracefile):
    file_name = "%s/%s" % (pattern_path, new_tracefile)
    target_name = "./transaction.txt"
    ret = 0
    try:
        cmd = "cp %s %s" % (file_name, target_name)
        ret = os.system(cmd)
        if ret == 0:
            print "- Success to replace %s by pattern(%s)" % (target_name, file_name)
        else:
            print "- Failed to replace %s by pattern(%s)" % (target_name, file_name)
    except Exception as e:
        print "- Failed to replace %s: %s" % (target_name, str(e))
    return ret


def update_configuration(new_traffic_pattern):
    pattern = '"%s"' % new_traffic_pattern
    cmd = "sed -i 's/traffic_pattern =.*/traffic_pattern = %s /g' define.py" % pattern
    ret = os.system(cmd)
    if ret == 0:
        print "- Success to update traffic pattern(%s)\n" % (new_traffic_pattern)
        pass
    else:
        print "- Failed to update traffic pattern(%s)\n" % (new_traffic_pattern)
    return ret


def main():
    new_tracefile = input_pattern()
    replace_transaction(new_tracefile)
    update_configuration(new_tracefile)


if __name__ == "__main__":
    main()
