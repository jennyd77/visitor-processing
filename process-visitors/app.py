import boto3
from decimal import Decimal
import json
import urllib
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
#import requests

client = boto3.client('rekognition')

# --------------- Helper Functions to call Rekognition APIs ------------------


def search_face_in_collection(collection_id,bucket,key):

    response=client.search_faces_by_image(CollectionId=collection_id,
                                Image={'S3Object':{'Bucket':bucket,'Name':key}},
                                FaceMatchThreshold=70,
                                MaxFaces=1)                            
    faceMatches=response['FaceMatches']
    if len(faceMatches) == 0:  # There is no match of this face in the collection
        return 0, 0
    else:
        # We know there is only one face in the photo;
        #  and just to be sure we have told search_faces_by_image to only return the best match.
        #  So we are VERY sure that there is only one match to process
        face_id=faceMatches[0]['Face']['FaceId']
        return 1, face_id


def add_faces_to_collection(bucket,key,collection_id):   

    response=client.index_faces(CollectionId=collection_id,
                                Image={'S3Object':{'Bucket':bucket,'Name':key}},
                                QualityFilter="AUTO",
                                MaxFaces=1)
    # We know there is only one face in the photo;
    #  and just to be sure we have told index_faces to only return one face.
    #  So we are VERY sure that there is only one face_id to read
    face_id=response['FaceRecords'][0]['Face']['FaceId']
    return face_id
    

# --------------- Main handler ------------------


def lambda_handler(event, context):
    '''Demonstrates S3 trigger that uses
    Rekognition APIs to detect faces, labels and index faces in S3 Object.
    '''
    #print("Received event: " + json.dumps(event, indent=2))
    #logger.info(json.dumps(event))

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    warrants_collection_id='warrants'
    victims_collection_id='victims'
    attendees_collection_id='attendees'
    try:   
        ##################################################################
        # Check if this is a new visitor or someone we've seen before
        ##################################################################
        response, face_id = search_face_in_collection(attendees_collection_id,bucket,key)
        if (response == 0):
            print("We have a new visitor, adding them to the visitors collection")
            face_id = add_faces_to_collection(bucket,key,attendees_collection_id)
            print("Updating DDB visitor table with new visitor with face_id ", face_id, "and S3 key ", key)
            # Implement code here to add new record for face_id
            # Are we directly updating the table, or are we sending the information to appsync?
        else:
            print("We have a visit by an known person. Incrementing counter in DDB for face_id ",face_id)
            # Implement code here to update DDB table by incrementing record for face_id
            # Are we directly updating the table, or are we sending the information to appsync?

        ##################################################################
        # Check if this is a victim of human trafficking
        ##################################################################
        response, face_id = search_face_in_collection(victims_collection_id,bucket,key)
        if (response == 0):
            print("All good, this person is not registered as a victim of human trafficking")
        else:
            print("Alert!!! We have found a potential victim of human trafficking")
            print("Send a victim alert with the face_id ", face_id, "and the S3 key ", key)
            # Implement code here to send the information to appsync

        ##################################################################
        # Check if there is an outstanding warrant for this person
        ##################################################################
        response, face_id = search_face_in_collection(warrants_collection_id,bucket,key)
        if (response == 0):
            print("All good, there are no outstanding warrants for this person")
        else:
            print("Alert!!! We have found a person of interest to the police")
            print("Send a warrant alert with the face_id ", face_id, "and the S3 key ", key)
            # Implement code here to send the information to appsync

        return 0
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e
