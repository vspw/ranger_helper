#!/usr/bin/python
import argparse
import requests
import sys
import string
import time
import json
import pprint
##import tid as acf2id
from requests.packages.urllib3.exceptions import InsecureRequestWarning
###################################################################################
##Example Invokations:-
## -- To print all existing kafka policies with the notion of personas
## -- add the script to include the password for the user in tidAuth function
## python3 ranger_helper.py --ranger_server_uri <ranger_host>:<port> --ranger_service_name myrepo_kafka --ranger_get_kafka_policies all
## TODO:-
## -- To print all existing HDFS policies into a file.
## python3 ranger_helper.py --ranger_server_uri <ranger_host>:<port> --ranger_service_name tech_hadoop --ranger_get_hdfs_policies all
## -- To set a bunch of HDFS policies using Ranger REST API
## python3 ranger_helper.py --ranger_server_uri <ranger_host>:<port> --ranger_service_name tech_hadoop --ranger_set_hdfs_policies ranger_policy_repo.json
##
##
####################################################################################

RANGER_DOMAIN = "null"
RANGER_SERVICE= "null"
def tidAuth():
    '''Authentication using ACF2ID and password'''
    tid='admin'
    pwd='xxxxx'
    auth=(tid, pwd)
    return auth


def rangerREST( restAPI ) :
    ## TODO Verify received code = 200 or else produce an error
    url = "https://"+RANGER_DOMAIN+restAPI
    print ("URL request = %s" % (url))
    s = requests.Session()
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    s.auth = tidAuth()
    r= s.get(url, verify=False)
    s.close()
    return(json.loads(r.text))

def rangerPOST( restAPI, data) :
    url = "https://"+RANGER_DOMAIN + restAPI
    ##print (url)
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    s = requests.Session()
    s.auth = tidAuth()
    r = s.post(url,json=data, verify=False)
    s.close()
    return (json.loads(r.text))


def parse_args():
    """Atlas Associate Tags: ParseArugument Function."""
    parser = argparse.ArgumentParser()
    parser.description = __doc__
    parser.add_argument('--ranger_server_uri', required=True, help="Ranger URI is required to communicate with Ranger Admin. Eg: zulu.hdp.com:6080")
    parser.add_argument('--ranger_service_name', required=True, help="RangerServiceName against which the policy is being queried. Eg: tech_hadoop,tech_hbase")
    parser.add_argument('--ranger_set_hdfs_policies', required=False, help="Pass a valid json file with appropriate policies to set")
    parser.add_argument('--ranger_get_hdfs_policies', required=False, help="Pass a comma separated list of policy numbers to get")
    parser.add_argument('--ranger_delete_hdfs_policies', required=False, help="Pass a comma separated list of policies to delete")
    parser.add_argument('--ranger_get_kafka_policies', required=False, help="Pass a valid json file with appropriate policies to set")
    return parser.parse_args()


def print_args(ranger_server_uri, ranger_hdfs_json):
    """Atlas Associate Tags: Prints All Arguments parsed """
    ##print ('Parsed these arguments: %s, %s' % (ranger_server_uri, ranger_function))


def set_hdfs_policies(ranger_policies_json):
    """Ranger importing Policies from Json file """
    ##curl -iv -u admin:admin -d @policy.json -H "Content-Type: application/json" -X POST http://zulu.hdp.com:6080/service/public/api/policy/
    ##print(json.dumps(ranger_policies_json))
    for var_policy in ranger_policies_json["HDFS_Policies"]:
        print("########################"+json.dumps(var_policy["policyName"])+"############################")
        updatedHDFSRepo = rangerPOST("/service/public/api/policy/", var_policy)
        print(json.dumps(updatedHDFSRepo))

def get_hdfs_policies(policy_list):
    """Ranger Get Specific Policies or All policies """
    var_policies=policy_list.split(",")
    print ("Parsing these policies: %s" %(var_policies))
    for var_policy in var_policies:
        if(var_policy.lower() == "all"):
            var_policy_json=rangerREST("/service/public/v2/api/service/%s/policy/" %(RANGER_SERVICE))
            print("PRINTING ALL POLICIES")
            data=json.dumps(var_policy_json)
            timestr = time.strftime("%Y%m%d-%H%M%S")
            with open('hdfs_policies'+timestr+'.json', 'w') as file:
                json.dump(var_policy_json, file)
            break
        var_policy_json=rangerREST("/service/public/v2/api/policy/%s" % (var_policy))
        print(var_policy_json)
    return

def delete_hdfs_policies(policy_list):
    print("Deleting said polices: %s" %(policy_list))

def validate_policy_json(hdfs_policies_json):
    flag_warn=None
    ##Iterate all the policies defined in the json file
    for var_policy in hdfs_policies_json["HDFS_Policies"]:
        ##For each policy defined, iterate over the listed HDFS resource paths
        for var_path in var_policy["resourceName"].split(","):
            ##verify if the resouce path is already existing in any Policy
            var_exiting_policy=rangerREST("/service/public/v2/api/service/%s/policy?resource:path=%s" % (RANGER_SERVICE,var_path))
            if (len(var_exiting_policy) > 0):
                flag_warn=True
                ##Just send a notification to inform the user.
                print("INFO: %s HDFS path already exists in the following Policy(s):-" %(var_path))
                ##List the policies where the path is already existing
                for var_entry in var_exiting_policy:
                    print(var_entry["name"])

    #Get User Confirmation before successfully validating the json file
    if (flag_warn == True):
        while True:
            input = (query_yes_no("Do you wish to continue with creating new ACLs? (y/n):"))
            if input in ['True','False']:
                break
        if (input == 'True'):
            ##if user wants to continue continue with next HDFS PATH
            return 1
        else:
            ##if user doesn't want to continue, simply exit without creating any ACLs
            print("returning 0")
            return 0
    return 1

def query_yes_no(question, default="yes"):
    # raw_input returns the empty string for "enter"
    yes = set(['yes','y', 'ye', ''])
    no = set(['no','n'])
    choice = input(question).lower()
    if choice in yes:
        print("returning True")
        return "True"
    elif choice in no:
        print("returning False")
        return "False"
    else:
        sys.stdout.write("Please respond with 'yes' or 'no'")
        return "BadInput"


def replace_repository_value(listOfDicts, key,value):
    for subVal in listOfDicts:
        subVal[key] = value
    return

def get_kafka_policies(policy_list):
    """Ranger Get Specific Policies or All policies """
    var_policies=policy_list.split(",")
    print ("Parsing these policies: %s" %(var_policies))
    for var_policy in var_policies:
        if(var_policy.lower() == "all"):
            var_policy_json=rangerREST("/service/public/v2/api/service/%s/policy/" %(RANGER_SERVICE))
            print("PRINTING ALL POLICIES")
            data=json.dumps(var_policy_json)
            timestr = time.strftime("%Y%m%d-%H%M%S")
            with open('kafka_policies'+timestr+'.json', 'w') as file:
                json.dump(var_policy_json, file)
            break
    print(json.dumps(var_policy_json,indent=2))
    var_str_json = json.dumps(var_policy_json,indent=2)
    json_obj =json.loads(var_str_json)
    READWRITE_SET={"publish","consume"}
    READONLY_SET={"consume"}
    WRITEONLY_SET={"publish"}

    ##POLICY IS ASSOCIATED WITH AN ID AND RESOURCE
    for policy in json_obj:
        PERSONAS= dict()
        READWRITE_PERSONAS=set()
        READONLY_PERSONAS=set()
        WRITEONLY_PERSONAS=set()
        OTHER_PERSONAS=set()

        PERSONAS["READWRITE_PERSONAS"]=READWRITE_PERSONAS
        PERSONAS["READONLY_PERSONAS"]=READONLY_PERSONAS
        PERSONAS["WRITEONLY_PERSONAS"]=WRITEONLY_PERSONAS
        PERSONAS["OTHER_PERSONAS"]=OTHER_PERSONAS


        #A POLICY HAS MULTIPLE ITEMS, EACH CAN HAVE SEPARATE PERMS
        for pol_item in policy["policyItems"]:
            access_perm_set = set()
            for access_item in pol_item["accesses"]:
                access_perm_set.add(access_item["type"])
            if(access_perm_set.issuperset(READWRITE_SET)):
                updatePERSONASSet(READWRITE_PERSONAS,pol_item)
            elif(access_perm_set.issuperset(READONLY_SET)):
                updatePERSONASSet(READONLY_PERSONAS,pol_item)
            elif(access_perm_set.issuperset(WRITEONLY_SET)):
                updatePERSONASSet(WRITEONLY_PERSONAS,pol_item)
            else:
                updatePERSONASSet(OTHER_PERSONAS,pol_item)

        # print("###################################")
        # print("ID    : "+str(policy["id"]))
        # print("Name  : "+policy["name"])
        # print("Topics: "+str(policy["resources"]["topic"]["values"]))
        printAllPolicyDetailsAndPersonas(policy,PERSONAS)
    return

def updatePERSONASSet(input_set,item):
    input_set.update(item["users"])
    input_set.update(item["groups"])
    return


def printAllPolicyDetailsAndPersonas(obj_policy,dict_PERSONAS):
    policyStr=str(obj_policy["id"])+"|"+obj_policy["name"]+"|"+str(obj_policy["resources"]["topic"]["values"])
    for key,val in dict_PERSONAS.items():
        # print(key, "=>", val)
        if(len(set(val))==0):
            val="none"
        policyStr+="|"+str(val)
    print(policyStr)
    return

def main():
    args = parse_args()
    global RANGER_DOMAIN
    global RANGER_SERVICE
    RANGER_DOMAIN = args.ranger_server_uri
    RANGER_SERVICE = args.ranger_service_name
    # Commenting the follow as we are not doing anything with HDFS policies

    # if args.ranger_set_hdfs_policies is not None:
    #     with open(args.ranger_set_hdfs_policies) as fh:
    #         hdfs_policies_json=json.load(fh)
    #     replace_repository_value(hdfs_policies_json["HDFS_Policies"],"repositoryName",RANGER_SERVICE)
    #     ##replace repository value can also be used to disable all the new policies if required
    #     if (validate_policy_json(hdfs_policies_json)):
    #         print("Setting HDFS Policies")
    #         print(hdfs_policies_json["HDFS_Policies"])
    #         set_hdfs_policies(hdfs_policies_json)

    if args.ranger_get_hdfs_policies is not None:
        get_hdfs_policies(args.ranger_get_hdfs_policies)
    elif args.ranger_delete_hdfs_policies is not None:
        delete_hdfs_policies(args.ranger_delete_hdfs_policies)
    elif args.ranger_get_kafka_policies is not None:
        get_kafka_policies(args.ranger_get_kafka_policies)
    else:
        print("Please read Usage!!")

if __name__ == '__main__':
    main()
