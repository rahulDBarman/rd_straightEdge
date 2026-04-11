import maya.api.OpenMaya as om
import maya.cmds as cmds
 
 
#rd_straight_edge(scale_value=0.4)
 
###################################################################################
def rd_straight_edge(scale_value=1):
    # Get the current selection
    selection = om.MGlobal.getActiveSelectionList()
 
    #selection = om.MGlobal.getActiveSelectionList()
    mdagPath = selection.getDagPath(0)
 
    selected_edges = []
    selected_vertex = []
 
    # Collect selected edges and their vertices
    for i in range(selection.length()):
        dagPath, component = selection.getComponent(i)
 
        if component.apiType() == om.MFn.kMeshEdgeComponent:
            edge_iter = om.MItMeshEdge(dagPath, component)
            while not edge_iter.isDone():
                edge_index = edge_iter.index()
                vtx0 = edge_iter.vertexId(0)
                vtx1 = edge_iter.vertexId(1)
 
                selected_edges.append(edge_index)
                selected_vertex.append([vtx0, vtx1])  # Use set for easy comparison
 
                edge_iter.next()
 
    #Find connedted vertex form selected edges
    vertex_list = find_connected_paths(selected_vertex)
 
    for vertex in  vertex_list:
        chainVerts = vertex
        # Get start and end positions
        startVert = chainVerts[0]
        endVert = chainVerts[-1]
 
        meshFn = om.MFnMesh(mdagPath)
        fullPath = mdagPath.fullPathName()
 
        startPoint = om.MVector(meshFn.getPoint(startVert, om.MSpace.kWorld))
        endPoint = om.MVector(meshFn.getPoint(endVert, om.MSpace.kWorld))
 
 
        # Calculate midpot start and end vertex
        mPoint = (startPoint + endPoint)/2
        midPoint = ( mPoint.x, mPoint.y, mPoint.z )
 
        # Get normals at start and end vertices
        startNormal = meshFn.getVertexNormal(startVert, False, om.MSpace.kWorld)
        endNormal = meshFn.getVertexNormal(endVert, False, om.MSpace.kWorld)
 
        avg_normal = (startNormal + endNormal).normalize()
 
        rotation = get_rotation_from_points(startPoint, endPoint, avg_normal)
 
 
        vertes = []
        # Move intermediate vertices to create straight line
        for i in range(1, len(chainVerts) - 1):  
            vertexName = fullPath + ".vtx[" + str(chainVerts[i]) + "]"
            vertes.append(vertexName)
 
        cmds.scale(
            1-scale_value, 1, 1,
            vertes,
            xformConstraint = "edge",
            constrainAlongNormal = True, pivot = midPoint,
            orientAxes =  rotation,
            )
     
    #om.MGlobal.setActiveSelectionList(selection)
 
        # test locator snap
        #cmds.setAttr( "locator1.t", midPoint[0], midPoint[1], midPoint[2] )
        #cmds.setAttr( "locator1.r", rotation[0], rotation[1], rotation[2] )
        #cmds.setAttr( "locator1.r", avg_normal[0], avg_normal[1], avg_normal[2] )
 
 
 
##################################
def find_connected_paths(edges):
    """
    Find all connected components with vertices in sequential path order.
    Returns list of paths where each path goes from start to end vertex.
    """
    # Build adjacency list
    graph = {}
    for v1, v2 in edges:
        if v1 not in graph:
            graph[v1] = []
        if v2 not in graph:
            graph[v2] = []
        graph[v1].append(v2)
        graph[v2].append(v1)
     
    visited = set()
    paths = []
     
    for vertex in graph:
        if vertex in visited:
            continue
         
        # Find all vertices in this component
        component = set()
        stack = [vertex]
        while stack:
            v = stack.pop()
            if v in component:
                continue
            component.add(v)
            for neighbor in graph[v]:
                if neighbor not in component:
                    stack.append(neighbor)
         
        # Find endpoint (vertex with 1 connection) or use first vertex
        start = vertex
        for v in component:
            if len(graph[v]) == 1:
                start = v
                break
         
        # Build sequential path
        path = [start]
        visited.add(start)
        current = start
         
        while True:
            next_v = None
            for neighbor in graph[current]:
                if neighbor not in visited:
                    next_v = neighbor
                    break
            if next_v is None:
                break
            path.append(next_v)
            visited.add(next_v)
            current = next_v
         
        paths.append(path)
     
    return paths
 
############################
def get_rotation_from_points(pointA, pointB, up_vector=(1, 0, 0)):
    """
    Calculate the rotation (as a quaternion) in Maya that points from pointA to pointB
    using a given up vector.
     
    Parameters:
    - pointA: tuple or list [x, y, z], start point
    - pointB: tuple or list [x, y, z], target point
    - up_vector: tuple or list, defaults to Y-up (0,1,0)
     
    Returns:
    - MQuaternion representing the rotation
    """   
 
    # Step 1: Direction vector from pointA to pointB
    forward = pointB - pointA
    if forward.length() == 0:
        raise ValueError("PointA and PointB cannot be the same")
    forward.normalize()
 
    # Step 2: Compute right vector and true up vector to form a rotation matrix
    right = up_vector ^ forward  # cross product
    right.normalize()
    true_up = forward ^ right
 
    # Step 3: Build rotation matrix
    rot_matrix = om.MMatrix()
    # OpenMaya uses row-major indexing in MMatrix:
    # Set columns for right, up, forward
    rot_matrix[0] = right.x
    rot_matrix[1] = right.y
    rot_matrix[2] = right.z
    rot_matrix[4] = true_up.x
    rot_matrix[5] = true_up.y
    rot_matrix[6] = true_up.z
    rot_matrix[8] = forward.x
    rot_matrix[9] = forward.y
    rot_matrix[10] = forward.z
 
    # Step 4: Convert rotation matrix to quaternion
    mtrans = om.MTransformationMatrix(rot_matrix)
    quat = mtrans.rotation(asQuaternion=True)
 
    euler_rot = quat.asEulerRotation()
 
    rotation = []
    rotation.append(int(om.MAngle(euler_rot.x).asDegrees()))
    rotation.append(int(om.MAngle(euler_rot.y).asDegrees()))
    rotation.append(int(om.MAngle(euler_rot.z).asDegrees()))
 
    return rotation
 
 
