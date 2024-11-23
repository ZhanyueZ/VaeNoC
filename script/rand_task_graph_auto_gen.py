import random 
import networkx as nx 
import os
import numpy as np
import re



NUM_NODES = 8
NUM_EDGES = 8
NUM_GRAPHS = 100
OUTPUT_DIR = "./LACG/"
SEQ_DIR = "./SEQ"
given_graph_edges = {
    (0, 2, 128),
    (0, 1, 64),
    (2, 3, 64),
    (1, 5, 64),
    (3, 4, 64),
    (5, 6, 64),
    (4, 6, 64),
    (6, 7, 64)
}

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SEQ_DIR,exist_ok=True)
########################################################## NOTE: THIS IS FROM OTHER PAPER'S METHOD #####
def GetTrafficMat(file_path_nomap,file_path_withmap, m ,flow_ratio):
    
    file_nomap = open(file_path_nomap,'r')
    file_withmap = open(file_path_withmap,'r')
    con_nomap = file_nomap.readlines()[0:] 
    con_withmap = file_withmap.readlines()[0:]
    file_nomap.close()
    file_withmap.close()

    SrcDst = []
    for item in con_nomap:
        item = item.strip().split(' ')
        item = list(map(float,item))
        SrcDst.append(item)
    
    CoreTile = []
    for item in con_withmap:
        item = item.strip().split(' ')
        item = list(map(float,item))
        CoreTile.append(item)
     
    CoreTile = np.array(CoreTile)
    SrcDst = np.array(SrcDst)
    CoreIdx = CoreTile[:,0]
    TileIdx = CoreTile[:,1]
    CorePair = SrcDst[:,0:2]

    for item in np.nditer(CorePair, op_flags=['readwrite']):
        for i in range(0,CoreTile.shape[0]):
            if(item == CoreIdx[i]):
                item[...] = TileIdx[i] 
                break
    
    SrcDst[:,2] = SrcDst[:,2]/flow_ratio
    source = SrcDst[:,0]
    dest = SrcDst[:,1]
    weight = SrcDst[:,2]
    
    TrafficMat = np.zeros((m,m))
    for i in range(SrcDst.shape[1]):
        sj = int(source[i]%m)
        si = int((source[i]-sj)/m)
        dj = int(dest[i]%m)
        di = int((dest[i]-dj)/m)

        if(si<di):
            # go right
            while(si!=di):
                si = si+1
                TrafficMat[si][sj] = TrafficMat[si][sj]+weight[i]
        elif(si>di):
            while(si!=di):
                si = si-1
                TrafficMat[si][sj] = TrafficMat[si][sj]+weight[i]
                
        # Y routing
        if(sj<dj):
            while(sj!=dj):
                sj = sj+1
                TrafficMat[si][sj] = TrafficMat[si][sj]+weight[i]
        elif(sj>dj):
            while(sj!=dj):
                sj = sj-1
                TrafficMat[si][sj] = TrafficMat[si][sj]+weight[i]
                
        if(si!=di or sj!=dj):
            print("Error Routing")

    return TrafficMat

def PCA(TrafficMat,n):
    meanVal=np.mean(TrafficMat,axis=0)     
    newData=TrafficMat-meanVal
    covMat=np.cov(newData,rowvar=0)    
    eigVals,eigVects=np.linalg.eig(np.asmatrix(covMat)) 
    eigValIndice=np.argsort(eigVals)               
    n_eigValIndice=eigValIndice[-1:-(n+1):-1]     
    n_eigVect=eigVects[:,n_eigValIndice]           
    lowDDataMat=newData*n_eigVect                  
    reconMat=(lowDDataMat*n_eigVect.T)+meanVal    
    LowDMat = lowDDataMat
    return LowDMat
    
def Covert2Vec(LowDMat):
    LowDMat = np.absolute(LowDMat)
    Vec = LowDMat.flatten()
    #print(LowDMat.shape)
    return Vec

def FeatureExtract(filepath1,filepath2, m, n, flow_ratio):
    TrafficMat = GetTrafficMat(filepath1, filepath2, m, flow_ratio)
    LowMat1 = PCA(TrafficMat,n)
    LowDMat = PCA(LowMat1.T,n)
    Vec = Covert2Vec(LowDMat)
    return Vec
#####################################################################################################################

def generate_random_graph(num_nodes, num_edges):
    graph = nx.Graph()
    graph.add_nodes_from(range(num_nodes)) 
    
    while len(graph.edges) < num_edges:
        u, v = random.sample(range(num_nodes), 2)
        weight = random.choice([64, 128]) 
        if not graph.has_edge(u, v):
            graph.add_edge(u, v, weight=weight)
    return graph

def save_graph_to_file(graph, filename):
    with open(filename, "w") as f:
        for u, v, d in graph.edges(data=True):
            f.write(f"{u} {v} {d['weight']}\n")








mesh_map = "./PIP_LACG_MAP"
m = 3 
n = 3
flow_ratio = 12800
training_graphs = []
for i in range(NUM_GRAPHS):
    arr = np.array(np.zeros((1,9)))
    while True:
        graph = generate_random_graph(NUM_NODES, NUM_EDGES)
        edge_set = {(u, v, d['weight']) for u, v, d in graph.edges(data=True)}
        if edge_set != given_graph_edges:  
            break
    training_graphs.append(graph)
    filename = os.path.join(OUTPUT_DIR, f"task_graph_{i + 1}.txt")
    save_graph_to_file(graph, filename)
    arr[0] = FeatureExtract(filename,mesh_map, m, n, flow_ratio)
    seqpath = os.path.join(SEQ_DIR,f"mesh_seq_{i+1}.txt")
    np.savetxt(seqpath,arr)

print(f"Generated {len(training_graphs)} random task graphs, saved to '{OUTPUT_DIR}'")