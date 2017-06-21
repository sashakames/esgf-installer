'''
ESGF Distribution Mirrors Utilities
'''
import os
import subprocess
import requests
import stat
import logging
from collections import OrderedDict
from esg_init import EsgInit

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
config = EsgInit()

# List of mirror location
esgf_dist_mirrors_list=("distrib-coffee.ipsl.jussieu.fr/pub/esgf","dist.ceda.ac.uk/esgf", "aims1.llnl.gov/esgf","esg-dn2.nsc.liu.se/esgf")

def generate_response_array(install_type):
    """ Check """
    response_array = {}
    for mirror in esgf_dist_mirrors_list:
        if install_type == "devel":
            response_array[mirror] = subprocess.Popen("curl -s -L --insecure %s/dist/devel/lastpush.md5|tr -s " "|cut -d " " -f1" % (mirror), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            response_array[mirror] = subprocess.Popen("curl -s -L --insecure %s/dist/lastpush.md5|tr -s " "|cut -d " " -f1" % (mirror), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    return response_array

def get_success_or_fail_reponses():
    """ Return a dictionary tuple with seccessful and 
    unseccessful response times from mirrors. 
    """
    response_times = {} # Successful connections 
    failed_requests = {} # Unsuccessful connection 

    for mirror in esgf_dist_mirrors_list:
        logger.debug("mirror: %s", mirror)
        host, page = mirror.rsplit("/", 1)
        logger.debug("host: %s", host)
        logger.debug("page: %s", page)

        try:
            response = requests.get("http://"+host, timeout=4.0)
            logger.debug("%s response time %s", host, response.elapsed)
            response_times[mirror] = response.elapsed
        except requests.exceptions.Timeout:
            logger.warn("%s request timed out", host)
            failed_requests[mirror] = "Request timed out"

    return (response_times,failed_requests)

def order_response_time():
    """ Sort the response time of mirrors and return a list of them."""
    return OrderedDict(sorted(response_times.items(), key=lambda x: x[1]))

def get_esgf_dist_mirror(mirror_selection_mode, install_type = None):
    """ Return the nearest mirror available. """

    # Generate response array 
    response_array = generate_response_array(install_type)

    # Get success and failed response 
    response_times, failed_requests = get_success_or_fail_reponses()

    # Order the response time of the mirrors 
    ranked_response_times = order_response_time()
    logger.debug("ranked_response_times: %s", ranked_response_times)

    master = response_array['distrib-coffee.ipsl.jussieu.fr/pub/esgf'] # get value of hard coded mirror 
    fastest = ranked_response_times.items()[0][0] # get the first element of the list
    logger.debug("fastest: %s", fastest)

    outofsync = False
    if response_array[fastest] != master:
        print "%s is the fastest mirror, but is out-of-sync, hence overlooked" % fastest
        outofsync = True
  
    if outofsync == True:
        # config.config_dictionary["esgf_dist_mirror"] = "http://distrib-coffee.ipsl.jussieu.fr/pub/esgf"
        return "http://distrib-coffee.ipsl.jussieu.fr/pub/esgf"
   
    try:
        if stat.S_ISFIFO(os.stat("/tmp/inputpipe").st_mode) != 0:
            print "using the fastest mirror %s" % ranked_response_times.items()[0][0]
            # config.config_dictionary["esgf_dist_mirror"] = ranked_response_times.items()[0][0]
            return ranked_response_times.items()[0][0]
    except OSError, error:
        logger.warning(error)


    logger.debug("mirror_selection_mode: %s", mirror_selection_mode)
    if mirror_selection_mode == "interactive":
        while True:
            try:
                _render_distribution_mirror_menu(ranked_response_times)
                choice = _select_distribution_mirror()
                logger.debug("choice result: %s", ranked_response_times.items()[choice][0])
                # config.config_dictionary["esgf_dist_mirror"] = ranked_response_times.items()[choice][0]
                return ranked_response_times.items()[choice][0]
            except IndexError, error:
                logger.error("Invalid selection", exc_info=True)
                continue
            break
    else:
        # config.config_dictionary["esgf_dist_mirror"] = ranked_response_times.items()[0][0]
        return ranked_response_times.items()[0][0]


def _render_distribution_mirror_menu(distribution_mirror_choices):
    print "Please select the ESGF distribution mirror for this installation (fastest to slowest): \n"
    print "\t-------------------------------------------\n"
    for index, (key, _) in enumerate(distribution_mirror_choices.iteritems(),1):
        print "\t %i) %s" % (index, key)
    print "\n\t-------------------------------------------\n"

def _select_distribution_mirror():
    choice = int(raw_input("Enter mirror number: "))
    #Accounts for off by 1 error
    choice = choice - 1
    return choice