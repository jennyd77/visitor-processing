import boto3
import urllib
import requests
import time
import json

client=boto3.client('rekognition')

victims_identified_table = "Victims_identified_temp"
warrants_identified_table = "Warrants_Identified_Temp"
attendees_table = "Uniqueattendees_Temp"
warrants_registered_table = "warrants_registered_table"
victims_registered_table = "Victims_Register_Temp"


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
   # ExternalImageId = key.replace("/","")
    response=client.index_faces(CollectionId=collection_id,
                                Image={'S3Object':{'Bucket':bucket,'Name':key}},
                                ##ExternalImageId = ExternalImageId,
                                QualityFilter="AUTO",
                                DetectionAttributes=['ALL'])

    print ('Results for ' + key) 	
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

def insert_dynamodb(DynamoDict):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TableName)
    response = table.put_item(
       Item= DynamoDict
    )
    return response

def get_facenamedynamodb(FaceId,TableName):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TableName)
    response = table.get_item(Key={'FaceID': FaceId})
    return response['Item']


def sendto_appsync(json_payload,url):
    r = requests.post(url, json={'query': json_payload})
    print(r.status_code)



def add_to_victims_identified(bucket,key):
    victims_collection_id='victims'
    response, face_id = search_face_in_collection(victims_collection_id,bucket,key)
    if response == 0:
        print("no victim match found")
    else:
        print("Alert!!! We have found a potential victim of human trafficking")
        thisdict = {
                "table": "victims_identified",
                "operation": "insert",
                "payload": {
                        "Latest_Timestamp":Timestamp,
                        "Face_id":face_id,
                        "Face_name":Face_name,
                        "Face_location_S3":S3_Location
                    }
                }
        appsync_output = json.dumps(thisdict)
        sendto_appsync(appsync_output,url)

def add_to_criminals_identified(bucket,key):
        warrants_collection_id='warrants' 
        response, face_id = search_face_in_collection(add_to_criminals_identified,bucket,key)
        if response == 0:
                 print("no criminals match found")
        else:
            thisdict = {
                "table": "warrants_identified",
                "operation": "insert",
                "payload": {
                        "Latest_Timestamp":Timestamp,
                        "Face_id":face_id,
                        "Face_name":Face_name,
                        "Face_location_S3":S3_Location
                    }
                }
            sendto_appsync(thisdict,'warrants')



def add_to_attendees_identified(collection_id,bucket,key):
    attendees_collection_id='attendees'
    response, face_id = search_face_in_collection(attendees_collection_id,bucket,key)
    S3_Location = bucket + "/" + key
    if (response == 0) :
        print("We have a new visitor, adding them to the visitors collection")
        print("Updating DDB visitor table with new visitor with face_id ", face_id, "and S3 key ", S3_Location)
        add_faces_to_collection(bucket,key,attendees_collection_id)
        thisdict =  {
                        'Latest_Timestamp':Timestamp,
                        'Face_id':face_id,
                        'Face_name':face_name,
                        'Face_location_S3':S3_Location,
                        'Numberofvisits':1
                    }
        json.dumps('thisdict')
   
        sendto_appsync(thisdict,'attendees')
    else:
        thisdict = {
                "table": "attendees",
                "operation": "update",
                "payload": {
                        "Timestamp":Timestamp,
                        "Face_id":face_id,
                        "Face_name":Face_name,
                        "Face_location_S3":S3_Location,
                        "NumberofVisits": TotalNumberofVisits
                    }
                }
        sendto_appsync(thisdict,'attendees')


def main():
    bucket='djennys-hackathon-team'
    collection_id='attendees'
    key='AttendeeFaces/badgephoto.jpg'

    add_to_attendees_identified(collection_id,bucket,key)
    add_to_criminals_identified(bucket,key)
    add_to_victims_identified(bucket,key)


if __name__ == "__main__":
    main()

    