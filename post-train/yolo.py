# USAGE
# python yolo.py --image images/baggage_claim.jpg --yolo yolo-coco

# import the necessary packages
import numpy as np
import argparse
import time
import cv2
import os

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, default="images",
	help="path to input image")
ap.add_argument("-y", "--yolo", required=True, default="./",
	help="base path to YOLO directory")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
	help="minimum probability to filter weak detections")
ap.add_argument("-t", "--threshold", type=float, default=0.3,
	help="threshold when applyong non-maxima suppression")
args = vars(ap.parse_args())

# load the COCO class labels our YOLO model was trained on
labelsPath = os.path.sep.join([args["yolo"], "obj.names"])
LABELS = open(labelsPath).read().strip().split("\n")

# initialize a list of colors to represent each possible class label
np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
	dtype="uint8")

# derive the paths to the YOLO weights and model configuration
# weightsPath = os.path.sep.join([args["yolo"], "yolov4-tiny_best.weights"])
# configPath = os.path.sep.join([args["yolo"], "yolov4-tiny.cfg"])
weightsPath = os.path.sep.join([args["yolo"],"weights", "yolov4-obj_best.weights"])
configPath = os.path.sep.join([args["yolo"],"models", "yolov4-obj.cfg"])


# load our YOLO object detector trained on COCO dataset (80 classes)
print("[INFO] loading YOLO from disk...")
net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

images_periods = dict()
times = 10

for f in os.listdir(args["image"]):	
	if not '.jpg' in f:
		continue
	image_path = os.path.join(args["image"], f)
	image_name = image_path.split('/')[-1]
	images_periods.setdefault(image_name, [])

	# load our input image and grab its spatial dimensions
	image = cv2.imread(image_path)
	(H, W) = image.shape[:2]

	# determine only the *output* layer names that we need from YOLO
	ln = net.getLayerNames()
	ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
	print(image_name)
	# construct a blob from the input image and then perform a forward
	# pass of the YOLO object detector, giving us our bounding boxes and
	# associated probabilities
	for i in range(times):
		blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
			swapRB=True, crop=False)
		net.setInput(blob)
		start = time.time()
		layerOutputs = net.forward(ln)
		end = time.time()

		# show timing information on YOLO
		period = end - start
		print("[INFO] YOLO took {:.2f} ms and {} fps".format(period*1000, 1/period))
		images_periods[image_name].append(period)

	# initialize our lists of detected bounding boxes, confidences, and
	# class IDs, respectively
	boxes = []
	confidences = []
	classIDs = []

	# loop over each of the layer outputs
	for output in layerOutputs:
		# loop over each of the detections
		for detection in output:
			# extract the class ID and confidence (i.e., probability) of
			# the current object detection
			scores = detection[5:]
			classID = np.argmax(scores)
			confidence = scores[classID]

			# filter out weak predictions by ensuring the detected
			# probability is greater than the minimum probability
			if confidence > args["confidence"]:
				# scale the bounding box coordinates back relative to the
				# size of the image, keeping in mind that YOLO actually
				# returns the center (x, y)-coordinates of the bounding
				# box followed by the boxes' width and height
				box = detection[0:4] * np.array([W, H, W, H])
				(centerX, centerY, width, height) = box.astype("int")

				# use the center (x, y)-coordinates to derive the top and
				# and left corner of the bounding box
				x = int(centerX - (width / 2))
				y = int(centerY - (height / 2))

				# update our list of bounding box coordinates, confidences,
				# and class IDs
				boxes.append([x, y, int(width), int(height)])
				confidences.append(float(confidence))
				classIDs.append(classID)

	# apply non-maxima suppression to suppress weak, overlapping bounding
	# boxes
	idxs = cv2.dnn.NMSBoxes(boxes, confidences, args["confidence"],
		args["threshold"])

	# ensure at least one detection exists
	if len(idxs) > 0:
		classCounts = dict()
		# loop over the indexes we are keeping
		for i in idxs.flatten():
			classID = classIDs[i]
			label = LABELS[classID]
			if (classID not in classCounts):
				classCounts[classID] = 0
			classCounts[classID] = classCounts[classID] + 1

			# extract the bounding box coordinates
			(x, y) = (boxes[i][0], boxes[i][1])
			(w, h) = (boxes[i][2], boxes[i][3])

			# draw a bounding box rectangle and label on the image
			color = [int(c) for c in COLORS[classID]]
			cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
			
			text = "{}: {:.2f}%".format(label, 100*confidences[i])
			cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
				0.5, color, 2)
		
		for index, classID in enumerate(classCounts):
			label = LABELS[classID]
			count = classCounts[classID] 
			text = "{0}: {1}".format(label, count) 
			print(text)
			cv2.putText(image, text, (20, 20 + index*16), cv2.FONT_HERSHEY_SIMPLEX,
				0.5, [0,0,0], 2)
	# show the output image
	imageOutputPath = os.path.join('output',image_path.split('/')[-1] )
	print(imageOutputPath)
	cv2.imwrite(imageOutputPath, image)
	# cv2.imshow("Image", image)
	# cv2.waitKey(0)
	print('\n')

for name, periods  in images_periods.items():
	print(name, periods)
