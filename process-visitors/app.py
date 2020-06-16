import boto3
from decimal import Decimal
import json
import urllib
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


#import requests

print('Loading function')

rekognition = boto3.client('rekognition')


# --------------- Helper Functions to call Rekognition APIs ------------------


def search_face_in_collection(collection_id,bucket,key):

    client=boto3.client('rekognition')

  
    response=client.search_faces_by_image(CollectionId=collection_id,
                                Image={'S3Object':{'Bucket':bucket,'Name':key}},
                                FaceMatchThreshold=90,
                                MaxFaces=2)
                                
    faceMatches=response['FaceMatches']
    print ('Matching faces')
    for match in faceMatches:
            print ('FaceId:' + match['Face']['FaceId'])
            print ('Similarity: ' + "{:.2f}".format(match['Similarity']) + "%")
            print ('Match Found in' + collection_id )


def add_faces_to_collection(bucket,key,collection_id):   
    client=boto3.client('rekognition')
    ExternalImageId = key.replace("/","")

    response=client.index_faces(CollectionId=collection_id,
                                Image={'S3Object':{'Bucket':bucket,'Name':key}},
                                ExternalImageId = ExternalImageId,
                                QualityFilter="AUTO",
                                DetectionAttributes=['ALL'])

    print('Results for ' + key) 	
    print('Faces indexed:')						
    for faceRecord in response['FaceRecords']:
         print('  Face ID: ' + faceRecord['Face']['FaceId'])
         print('  Location: {}'.format(faceRecord['Face']['BoundingBox']))

    print('Faces not indexed:')
    for unindexedFace in response['UnindexedFaces']:
        print(' Location: {}'.format(unindexedFace['FaceDetail']['BoundingBox']))
        print(' Reasons:')
        for reason in unindexedFace['Reasons']:
            print('   ' + reason)
    return len(response['FaceRecords'])




# --------------- Main handler ------------------


def lambda_handler(event, context):
    '''Demonstrates S3 trigger that uses
    Rekognition APIs to detect faces, labels and index faces in S3 Object.
    '''
    #print("Received event: " + json.dumps(event, indent=2))
    #logger.info('## Event')
    logger.info(json.dumps(event))

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    logger.info(bucket)
    logger.info(key)
    warrants_collection_id='warrants'
    victims_collection_id='victims'
    attendees_collection_id='attendees'
    try:
        
        # Calls rekognition DetectFaces API to detect faces in S3 object
        response = search_face_in_collection(attendees_collection_id,bucket,key)

 

        # Print response to console.
        print(response)

        return response
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e
