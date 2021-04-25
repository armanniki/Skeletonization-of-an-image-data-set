from skimage import io
from skimage.filters import gaussian
from skimage.util import img_as_ubyte
import cv2
import os
from skimage import morphology
from skan import Skeleton, summarize
import pandas as pd

"""Full pipeline from raw images to skeleton and then excel file with edges and knots informations.
----------
This pipeline is subjected to do skeletonization and analyse skeletone in three steps:
STEP1 :
    image pre-processing to generate binerized images from raw TIFF images.

STEP2 :
     skeletonize the 3D image (image processing), and then analysing the skeletonized image.

STEP3 :
     making a data frame, omiting extra informations and saving in excel data.
-------
results : 
Excel files
1. "Branches_Data.xlsx" ,  and "KantenList.xlsx"
    A brief description of each column of "Branches_Data.xlsx" is as follows:
    skeleton-id :
        Each connected skeleton in the image gets a unique ID
        
    node-id-src, node-id-dst :
        Each branch starts and ends at specific nodes. These are the IDs of the start and end nodes. “src” and “dst” are short for “source” and “destination”.
    
    branch-distance :
        The distance, in real coordinates, along the skeleton, of this branch. (This is the same as the distance in pixels, multiplied by the spacing, but this can be slightly different if the spacing is different in x, y, and z.)
    
    branch-type :
        The branch-type is coded by number as:
            0. endpoint-to-endpoint (isolated branch)
            1. junction-to-endpoint
            2. junction-to-junction
            3. isolated cycle
        that the branch-types 0 and 3 are omitted, because they are meaningless in our case
        
    coord-src-0, coord-src-1, coord-src-2 :
        The coordinates of the source pixel, but taking the pixel spacing into account
        
    coord-dst-0, coord-dst-1, coord-dst-2 :
        Same, but for the destination pixel
        
    euclidean-distance :
        The straight-line distance between the source and destination pixels

2. "KnotenList.xlsx"
    A brief description of each column of "KnotenList.xlsx" is as follows:
    node-id-src :
        each node has a unic ID
    
    coord-src-0, coord-src-1, coord-src-2 :
        The coordinates of the each node, taking the pixel spacing into account

2. "KantenList.xlsx"
    A brief description of each column of "KantenList.xlsx" is as follows:
    node-id-src, node-id-dst :
        Each branch starts and ends at specific nodes. These are the IDs of the start and end nodes. “src” and “dst” are short for “source” and “destination”.
"""

# Path of the folder, where the tiff images are there
folder = '7_Tiff'

# Path of the folder, where the processed images would be stored
if not os.path.exists('7_Tiff_'):
    os.makedirs('7_Tiff_')
# STEP1
# Every image through this for loop would be smoothed, binerized and then stored in the next folder
# Sigma is a Parameter which is a trigger point to determine the grade of smoothing
# Thresholding is done by manual method, and the Threshold is selected case specific
for filename in os.listdir(folder):
    # Smoothing the image by Gaussian method
    im = io.imread(os.path.join(folder, filename))
    smooth = gaussian(im, sigma=0.5)
    smgr = img_as_ubyte(smooth)

    # Now thresholding the smoothed image
    ret,thresh1 = cv2.threshold(smgr,250,255,cv2.THRESH_BINARY)
    cv2.imwrite('7_Tiff_/_' + filename, thresh1)

# All images of the second folder, the processed one, would be read as a 3D array
im_collection = io.imread_collection('7_Tiff_/*.tiff', plugin='tifffile')
im_3d = im_collection.concatenate()
print("STEP1 is Done!")

# STEP2
# In this two lines the 3D array (iamge) is skeletonized, then the skeletonized image is analysed. "branch_data" is a summarization of all edges and knots informations
skeleton0 = morphology.skeletonize(im_3d)
branch_data = summarize(Skeleton(skeleton0))
print("STEP2 is Done!")

# STEP3
# In order to save the "branch_data" in an excel file and do some edits on it, it should be defined as a Data Frame.

df = branch_data

# This columns must be removed, because they do not have any usage in this work
column_list_to_remove = ['mean-pixel-value', 'stdev-pixel-value', 'image-coord-src-0', 'image-coord-src-1', 'image-coord-src-2', 'image-coord-dst-0', 'image-coord-dst-1', 'image-coord-dst-2']
df.drop(column_list_to_remove, axis=1, inplace = True)

df_mf = df[(df['branch-type']== 1) | (df['branch-type']== 2)]
df_mg = df[(df['branch-type']== 1) | (df['branch-type']== 2)]
df_mh = df[(df['branch-type']== 1) | (df['branch-type']== 2)]

# Generate a general branches Data Excel file from above Data Frame
writer = pd.ExcelWriter('Branches_Data.xlsx', engine='xlsxwriter')
df_mf.to_excel(writer, sheet_name='Sheet1')
writer.save()

# Generate a List of Nodes
df_knoten_src = df_mf
columns_to_remove_knoten_src = ['skeleton-id', 'node-id-dst', 'branch-distance', 'branch-type', 'coord-dst-0', 'coord-dst-1', 'coord-dst-2', 'euclidean-distance']
df_knoten_src.drop(columns_to_remove_knoten_src, axis=1, inplace = True)
Knoten_src_writer = pd.ExcelWriter('Knoten_src_List.xlsx', engine='xlsxwriter')
df_knoten_src.to_excel(Knoten_src_writer, sheet_name='Sheet1')
Knoten_src_writer.save()


df_knoten_dst = df_mg
columns_to_remove_knoten_dst = ['skeleton-id', 'node-id-src', 'branch-distance', 'branch-type', 'coord-src-0', 'coord-src-1', 'coord-src-2', 'euclidean-distance']
df_knoten_dst.drop(columns_to_remove_knoten_dst, axis=1, inplace = True)
df_knoten_dst.rename(columns = {'node-id-dst': 'node-id-src', 'coord-dst-0': 'coord-src-0', 'coord-dst-1': 'coord-src-1', 'coord-dst-2': 'coord-src-2'}, inplace=True)
Knoten_dst_writer = pd.ExcelWriter('Knoten_dst_List.xlsx', engine='xlsxwriter')
df_knoten_dst.to_excel(Knoten_dst_writer, sheet_name='Sheet1')
Knoten_dst_writer.save()



files_xlsx = ['Knoten_src_List.xlsx', 'Knoten_dst_List.xlsx']
df_knoten = pd.DataFrame()
for f in files_xlsx:
    data = pd.read_excel(f, 'Sheet1')
    df_knoten = df_knoten.append(data)
df_knoten = df_knoten.drop(columns=['Unnamed: 0'])
df_knoten.drop_duplicates(subset=["node-id-src"], inplace = True)
df_knoten.sort_values(by = "node-id-src", inplace=True)
#df_knoten = df_knoten.drop(columns=[' '])
Knoten_writer = pd.ExcelWriter('KnotenListt.xlsx', engine='xlsxwriter')
df_knoten.to_excel(Knoten_writer, sheet_name='Sheet1')
Knoten_writer.save()

import openpyxl
book= openpyxl.load_workbook('Knoten_Listt.xlsx')
sheet = book['Sheet1']
#delete column from existing sheet
sheet.delete_cols(1)
book.save('KnotenList.xlsx')


# Generate a List of Edges
df_kanten = df_mh
columns_to_remove_kanten = ['skeleton-id', 'branch-distance', 'branch-type', 'coord-src-0', 'coord-src-1', 'coord-src-2', 'coord-dst-0', 'coord-dst-1', 'coord-dst-2', 'euclidean-distance']
df_kanten.drop(columns_to_remove_kanten, axis=1, inplace = True)
Kanten_writer = pd.ExcelWriter('KantenList.xlsx', engine='xlsxwriter')
df_kanten.to_excel(Kanten_writer, sheet_name='Sheet1')
Kanten_writer.save()

print("STEP3 is Done!")

