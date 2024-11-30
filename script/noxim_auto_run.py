
import os
import csv

import concurrent.futures


NUM_APP = 100

# define the parameter list... The values are all in power.yaml
buffer_depth_list = [2,4,8,16,32,64]
flit_size = [16,32,64,128]
num_of_virtual_channel = [1,2,3,4,5,6,7,8] # maximum of VC is 8
r2h_link_length = [0.5,1.0,1.5,2.0,2.5,3.0]
r2r_link_length = [0.5,1.0,1.5,2.0,2.5,3.0]

cfg_dir = "/home/kenzoy0426/UT-24Fall/noxim/config_examples/pip_cfg"
cfg_gen_dir = "/home/kenzoy0426/UT-24Fall/noxim/config_examples/pip_cfg/pip_gen_cfg"
traffic_table_dir = "/home/kenzoy0426/UT-24Fall/noxim/bin/pip_traffic_table"
sim_result_path = "/home/kenzoy0426/UT-24Fall/noxim/pip_sim_results"
noxim_bin_path = "/home/kenzoy0426/UT-24Fall/noxim/bin"
task_graph_dir = "/home/kenzoy0426/UT-24Fall/noc_benchmark/script/LACG"
mapping_file_path = "/home/kenzoy0426/UT-24Fall/noc_benchmark/script/PIP_LACG_MAP"

cfg_template = os.path.join(cfg_dir,"pip_cfg.yaml")
tb_template = os.path.join(traffic_table_dir,"pip_traffic_table.txt")


def gen_traffic_table(task_graph,mapping_file,output_file,traffic_ratio):
    with open(task_graph, 'r') as f:
        task_graph = [
            (int(line.split()[0]), int(line.split()[1]), int(line.split()[2]))
            for line in f
        ]
    with open(mapping_file, 'r') as f:
        mapping = {
            int(line.split()[0]): int(line.split()[1])
            for line in f
        }
    replaced_graph = [
        (mapping[src], mapping[dst], weight/traffic_ratio)
        for src, dst, weight in task_graph
    ]
    with open(output_file, 'w') as f:
        for src, dst, weight in replaced_graph:
            f.write(f"{src} {dst} {weight:.4f}\n")
    

def update_cfg(path,output_path,**kwargs):
    with open(path,'r') as f:
        cfg_lines = f.readlines()

    updated_lines = []
    for line in cfg_lines:
        entry = line.strip()
        if entry.startswith('#') or entry == "":
            updated_lines.append(line)
            continue
        key = entry.split(":")[0].strip()
        if key in kwargs:
            updated_lines.append(f"{key}: {kwargs[key]}\n")
        else:
            updated_lines.append(line)

    with open(output_path,'w') as f:
        f.writelines(updated_lines)
    
    print(f"Updated configuration saved to: {output_path}")


# with any given traffic table, try all the parameters, generate the cfg, run simulation, get results
def auto_gen_cfg_and_output(i):
    # os.system(f"rm -f {cfg_gen_dir}/*")
    # os.system(f"rm -f {sim_result_path}/*")
    ttb_name = f"./pip_traffic_table/pip_traffic_table_app{i+1}.txt"
    task_graph_path = os.path.join(task_graph_dir,f"task_graph_{i+1}.txt")
    traffic_table_path = os.path.join(traffic_table_dir,f"pip_traffic_table_app{i+1}.txt")
    gen_traffic_table(task_graph_path,mapping_file_path,traffic_table_path,12800)

    csv_file = os.path.join(sim_result_path,f"sim_results_app{i+1}.csv")
    with open(csv_file, mode="w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Throughput", "Latency", "Power", "Buffer Depth", "Flit Size", "NUM_VC", "r2h_len","r2r_len"])
    os.chdir(noxim_bin_path)
    for buffer_depth in buffer_depth_list:
        for flit in flit_size:
            for vc in num_of_virtual_channel:
                for r2h in r2h_link_length:
                    for r2r in r2r_link_length:
                        suffix = f"bd={buffer_depth}_f={flit}_vc={vc}_r2h={r2h}_r2r={r2r}"
                        output_path = os.path.join(cfg_gen_dir,f"pip_cfg_{suffix}_app{i+1}.yaml")
                        update_cfg(cfg_template,output_path,buffer_depth=buffer_depth,flit_size=flit,n_virtual_channels=vc,r2h_link_length=r2h,r2r_link_length=r2r,traffic_table_filename = ttb_name)
                        cmd = f"./noxim -power ./power.yaml -config {output_path} -seed 1234"
                        process = os.popen(cmd)
                        simulation_output = process.read()
                        process.close()
                        for line in simulation_output.splitlines():
                            if "Network throughput (flits/cycle)" in line:
                                throughput = float(line.split(":")[1].strip())
                            elif "Global average delay (cycles)" in line:
                                average_latency = float(line.split(":")[1].strip())
                            elif "Total energy (J)" in line:
                                power = float(line.split(":")[1].strip())

                        with open(csv_file, mode="a", newline="") as csvfile:
                            csv_writer = csv.writer(csvfile)
                            csv_writer.writerow([throughput, average_latency, power,buffer_depth, flit,vc,r2h,r2r])
                            csvfile.flush()


# def gen_csv_for_all_app(num_of_app):
#     for i in range(1,100):
#         auto_gen_cfg_and_output(i)
def gen_csv_for_all_app(num_of_app):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(auto_gen_cfg_and_output, i) for i in range(1, num_of_app)]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result() 
            except Exception as e:
                print(f"Error occurred: {e}")


gen_csv_for_all_app(NUM_APP)




