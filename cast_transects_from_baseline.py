'''
Copyright 2017

@author: Phillipe Wernette

MORE INFORMATION ABOUT CASTING TRANSECTS VIA SCRIPTING:
https://geonet.esri.com/message/45970#comments
'''
import arcpy as ap
import datetime as dt
import math
import random
from functools import partial
from arcpy import env
env.overwriteOutput = True

''' This function creates a Feature Class to be used for generating transects '''
def create_fc(outpath, featclassname):
    i = dt.datetime.now()
    
    ap.CreateFeatureclass_management(outpath, str(featclassname) + "_" + str(i.year) + str(i.month) + str(i.day), "POLYLINE", spatial_reference="D:/coordinate systems/UTM_Zone_14N.prj")
    tmpfc = outpath + "/" + str(featclassname) + "_" + str(i.year) + str(i.month) + str(i.day)
    if featclassname == "transects":
        ap.AddField_management(tmpfc, "tid", "TEXT", "#", "#", "5")

''' This function searches for and delete any feature class in the specificed array '''
def clean_up(items):
    for clean in items:
        if ap.Exists(clean):
            ap.Delete_management(clean)

''' This function specifies whether transects are left, right, or both sides of a baseline

'''
#def lrb(tr_distance, start_x, start_y, delta_x, delta_y):

try:
    dtime = dt.datetime.now()

    # INPUT 1: Geodatabase path
    pathname = input("File Geodatabase Path: ")

    env.workspace = pathname
    #ap.env.workspace = "K:/ARP - What is a Dune/Dune Extraction Approaches.gdb"

    datasetList = ap.ListFeatureClasses()

    '''
    for dataset in datasetList:
        if "baseline" in str(dataset):
            print "TRUE"
            datasetList.remove(dataset)
        print str(dataset)
    '''

    # INPUT 2: Baseline feature class name
    bl_name = input("Baseline Feature Class Name: ")

    # Define the baseline and transect feature classes
    blfc = pathname + "/" + str(bl_name) + "_" + str(dtime.year) + str(dtime.month) + str(dtime.day)
    tfc = pathname + "/transects_" + str(dtime.year) + str(dtime.month) + str(dtime.day)
    

    # Continue if the baseline feature class exists
    if not(ap.Exists(blfc)):
        create_fc(pathname, str(bl_name))
    else:
        ap.Delete_management(blfc)
        create_fc(pathname, str(bl_name))


    ''' Draw the baseline '''
    # Define start and end points for the baseline
    bl_x1 = 661466.1
    #bl_x2 = 661466.1
    bl_x2 = 661266.1
    bl_y1 = 2980123.5
    bl_y2 = 2982585.5

    # Insert line geometry
    with ap.da.InsertCursor(blfc, ["SHAPE@"]) as icur:
        bl_array = ap.Array([ap.Point(bl_x1, bl_y1),
                             ap.Point(bl_x2, bl_y2)])
        bl_polyline = ap.Polyline(bl_array)
        icur.insertRow([bl_polyline])

    # Remove the InstertCursor (clean-up)
    del icur

    
    ''' Draw transects '''
    # INPUT 3: Direction from baseline
    #tr_dir = input("Direction from baseline (n, s, e, or w): ")

    # INPUT 4: Distance from baseline
    tr_dist = input("Distance from baseline (in meters): ")

    # INPUT 5: Distance between transects
    tr_spac = input("Distance between transects (in meters): ")

    # Create the transects feature class if it does not already exist
    if not ap.Exists(tfc):
        create_fc(pathname, "transects")
    else:
        ap.Delete_management(tfc)
        create_fc(pathname, "transects")

    diffx = abs(bl_x2 - bl_x1)
    diffy = abs(bl_y2 - bl_y1)

    if bl_y1<bl_y2:
        xc = bl_x1
        yc = bl_y1
    else:
        xc = bl_x2
        xc = bl_y2

    # Create index for transect id
    trid = 001


    ''' Cast trnasects from baseline '''
    if diffx != 0:
        trdx = tr_dist*math.sin(math.atan(diffy/diffx))
        trdy = tr_dist*math.cos(math.atan(diffy/diffx))

        bldx = tr_spac*math.cos(math.atan(diffy/diffx))
        bldy = tr_spac*math.sin(math.atan(diffy/diffx))

        with ap.da.InsertCursor(tfc, ("tid", "SHAPE@")) as icur:
            if bl_y1<bl_y2:
                while xc>bl_x2 and yc<bl_y2:
                    x2 = xc - trdx
                    y2 = yc - trdy

                    tr_array = ap.Array([ap.Point(xc, yc),
                                         ap.Point(x2, y2)])
                    tr_poly = ap.Polyline(tr_array)
                    icur.insertRow((trid, tr_poly))

                    trid = trid + 1
                    xc = xc - bldx
                    yc = yc + bldy
            '''else:
                while xc>bl_x1 and yc<bl_y1:'''
        del icur
    elif diffx == 0:
        # SPECIAL CASE: Vertical baseline (due N-S orientation)
        with ap.da.InsertCursor(tfc, ("tid", "SHAPE@")) as icur:
            if bl_y1<bl_y2:
                while yc<bl_y2:
                    x1 = xc
                    x2 = xc - tr_dist
                    
                    tr_array = ap.Array([ap.Point(x1, yc),
                                         ap.Point(x2, yc)])
                    tr_poly = ap.Polyline(tr_array)
                    icur.insertRow((trid, tr_poly))

                    trid = trid + 1
                    yc = tr_spac + yc
        del icur
    elif diffy == 0:
        # SPECIAL CASE: Horizontal baseline (due E-W orientation)
        with ap.da.InsertCursor(tfc, ("trid", "SHAPE@")) as icur:
            if bl_x1<bl_x2:
                while xc<bl_x2:
                    y1 = yc
                    y2 = yc + tr_dist
                    
                    tr_array = ap.Array([ap.Point(xc, y1),
                                         ap.Point(xc, y2)])
                    tr_poly = ap.Polyline(tr_array)
                    icur.insertRow((trid, tr_poly))

                    trid = trid + 1
                    xc = tr_spac + xc
        del icur


    ''' OPTIONAL: Output transect analysis '''
    outoption = input("Output transect analysis (y/n)? ")
    if outoption == 'y':
        # INPUT 6: Output file location
        logpath = input("Output file location: ")
        tblname = "transect_analysis_" + str(dtime.year) + str(dtime.month) + str(dtime.day)
        tbl = pathname + "/" + tblname
        
        # Open new output log file
        if ap.Exists(tbl):
            ap.Delete_management(tbl)
        ap.CreateTable_management(pathname, tblname)
        icur = ap.InsertCursor(tbl)

        # Output pipe-delimited text file
        logname = logpath + "/analysis_" + str(dtime.year) + str(dtime.month) + str(dtime.day) + "_" + str(dtime.hour) + str(dtime.minute) + ".csv"
        f = open(logname, "w")
        f.write("transect_id, intersect_id, xcoord, ycoord\n")

        # Clean up dataset list (remove baseline and transect feature classes)
        datasets = []
        for dataset in datasetList:
            if not "baseline" in str(dataset) and not "transect" in str(dataset):
                datasets.append((dataset, pathname + "/" + str(dataset)))
        del datasetList

        
        # ALTERNATIVE APPROACH TO ADDING FIELDS WITH SIMILAR ATTRIBUTES TO A TABLE/FC
        fields = ['tid', 'fc_intersect', 'x_coordinate', 'y_coordinate']

        addField = partial(
            ap.AddField_management,
            tbl,
            field_type="TEXT",
            field_length="30")

        for field in fields:
            addField(field)

        
        
        foo = 0
        for dat in datasets:
            # Temporary intersection feature class
            if ap.Exists(pathname + "/tmp"):
                ap.Delete_management(pathname + "/tmp")
            ap.CreateFeatureclass_management(pathname, "tmp", "POINT", spatial_reference="D:/coordinate systems/UTM_Zone_14N.prj")

            # Intersect Transects with each Feature Class
            ap.Intersect_analysis([tfc, dat[1]], pathname + "/tmp", "ALL", output_type="POINT")

            # Add X and Y coordinates to the Feature Class attributes
            ap.AddXY_management(pathname + "/tmp")

            # Open Search Cursor
            scur = ap.SearchCursor(pathname + "/tmp")

            # Extract values from intersected points feature class
            for s in scur:
                f.write(str(s.tid) + ',' + str(dat[0]) + ',' + str(s.POINT_X) + ',' + str(s.POINT_Y) + '\n')

            # Delete the intersected points Feature Class
            ap.Delete_management(pathname + "/tmp")

            del(scur)
        f.close()
        del(f, icur)
    '''
    with ap.da.InsertCursor(tfc, ["SHAPE@"]) as icur:
        for i in range(bl_y1, bl_y2):
    '''
except Exception as e:
   print(e)


'''
"K:/ARP - What is a Dune/Dune Extraction Approaches.gdb"
'''
