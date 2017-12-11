"""
Create a Human Intelligence Task in Mechanical Turk
"""
import boto3
import boto.mturk.connection
from boto.mturk.qualification import Qualifications, PercentAssignmentsApprovedRequirement, LocaleRequirement
import datetime
from AMT_parameters import get_boto2_parameters, get_URL_parameters
import sys

from create_hit_document import create_document
from create_crowdflower_hit_document import create_crowdflower_document

from insert_data_into_mongodb import get_data_path
from helper_functions import get_timestamp, get_log_directory

# REGION_NAME = 'us-east-1'
AWS_KEY_FILE = "./AWS_key/credentials"
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''

with open(AWS_KEY_FILE, "r") as credential_file:
    credentials = credential_file.read()
    AWS_ACCESS_KEY_ID = credentials.split('\n')[0]
    AWS_SECRET_ACCESS_KEY = credentials.split('\n')[1]
# ENDPOINT_URL = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

TITLE = "Identify Work-Related Details Of Tweets"
# DESCRIPTION = "External survey"
KEYWORDS = "Twitter, job and employment, employment status, annotation"
URL = "https://homanlab.org"
FRAME_HEIGHT = 700 # the height of the iframe holding the external hit
AMOUNT = .84

TOTAL_CROWDFLOWER_TWEETS = 100
XML_FILE_PATH = "./xml_files/mturk.xml"


def get_client(environment):
    """
    Function to get the mturk client
    :return: mturk client
    """
    client = boto.mturk.connection.MTurkConnection(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        host=get_boto2_parameters(environment)
    )
    return client


def get_requirement():
    """
    Function to set the requirements. This is optional.
    :return: list
    """
    qualifications = Qualifications()
    qualifications.add(PercentAssignmentsApprovedRequirement(comparator="GreaterThan", integer_value="90"))
    qualifications.add(LocaleRequirement("EqualTo", "US"))
    return qualifications


def get_xml_file():
    """
    Function to read and return file content
    :return: content of the file
    """
    question_file = open(XML_FILE_PATH, "r")
    return question_file.read()


def create_hit(logfile, environment, start_position=None, tweet_count=None):
    """
    Function to create a Human Intelligence Task in mTurk
    :return: None
    """

    client = get_client(environment)
    qualifications = get_requirement()
    # question = get_xml_file()
    questionform = boto.mturk.question.ExternalQuestion(URL, FRAME_HEIGHT)
    response = client.create_hit(
        title=TITLE,
        # description=DESCRIPTION,
        keywords=KEYWORDS,
        question=questionform,
        max_assignments=5,
        qualifications=qualifications,
        reward=boto.mturk.price.Price(amount=AMOUNT),
        lifetime=datetime.timedelta(minutes=14400),
        duration=datetime.timedelta(minutes=120),
        approval_delay= datetime.timedelta(minutes=14400),
        response_groups=('Minimal', 'HITDetail'),
        annotation='good'
    )

    hit_info = response[0]
    hit_type_id = hit_info.HITTypeId
    hit_id = hit_info.HITId
    if start_position is None:
        create_document(hit_id)
    else:
        create_crowdflower_document(hit_id, start_position, tweet_count)

    logfile.write("Your HIT ID is: {}\n\n".format(hit_id))

    return hit_type_id

if __name__ == '__main__':
    argument_length = len(sys.argv)

    logfile = open(get_log_directory('HITs') + get_timestamp() + '.txt', 'w')

    hit_type_id = ""
    if argument_length < 4:
        print("3 arguments required ....\n"
              "example: python script.py sandbox crowdflower 10..")
        sys.exit(0)

    environment = sys.argv[1]
    if sys.argv[2] == 'unlabeled':
        hit_type_id = create_hit(logfile, environment)
    if sys.argv[2] == 'crowdflower':
        tweet_count = int(sys.argv[3])
        for i in range((TOTAL_CROWDFLOWER_TWEETS/tweet_count)):
            hit_type_id = create_hit(logfile, environment, 5*i*tweet_count, tweet_count)

    logfile.write(get_URL_parameters(environment) + "{}\n".format(hit_type_id))
