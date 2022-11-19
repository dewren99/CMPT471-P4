import json

import networkx as nx

from app import NetworkApp
from rule import MatchPattern
from te_objs import PassByPathObjective, MinLatencyObjective, MaxBandwidthObjective
from utils_json import DefaultEncoder


class TEApp(NetworkApp):
    def __init__(self, topo_file, json_file, of_controller=None, priority=2):
        super(TEApp, self).__init__(
            topo_file, json_file, of_controller, priority)
        self.pass_by_paths_obj = []  # a list of PassByPathObjective objects
        self.min_latency_obj = []  # a list of MinLatencyObjective objects
        self.max_bandwidth_obj = []  # a list of MaxBandwidthObjective objects

    def add_pass_by_path_obj(self, pass_by_obj):
        self.pass_by_paths_obj.append(pass_by_obj)

    def add_min_latency_obj(self, min_lat_obj):
        self.min_latency_obj.append(min_lat_obj)

    def add_max_bandwidth_obj(self, max_bw_obj):
        self.max_bandwidth_obj.append(max_bw_obj)

    # This function reads the TE objectives in the `self.json_file`
    # Then, parses the JSON objects to the three list:
    #       self.pass_by_paths_obj
    #       self.min_latency_obj
    #       self.max_bandwidth_obj
    def from_json(self):
        with open('%s' % self.json_file) as f:
            json_dict = json.load(f)

            self.pass_by_paths_obj = []
            for obj in json_dict['pass_by_paths']:
                match_pattern = MatchPattern(**obj['match_pattern'])
                switches = [str(s) for s in obj['switches']]
                symmetric = obj['symmetric']
                pass_by_obj = PassByPathObjective(
                    match_pattern, switches, symmetric)
                self.pass_by_paths_obj.append(pass_by_obj)

            self.min_latency_obj = []
            for obj in json_dict['min_latency']:
                match_pattern = MatchPattern(**obj['match_pattern'])
                src_switch = obj['src_switch']
                dst_switch = obj['dst_switch']
                symmetric = obj['symmetric']
                min_lat_obj = MinLatencyObjective(
                    match_pattern, src_switch, dst_switch, symmetric)
                self.min_latency_obj.append(min_lat_obj)

            self.max_bandwidth_obj = []
            for obj in json_dict['max_bandwidth']:
                match_pattern = MatchPattern(**obj['match_pattern'])
                src_switch = obj['src_switch']
                dst_switch = obj['dst_switch']
                symmetric = obj['symmetric']
                max_bw_obj = MaxBandwidthObjective(
                    match_pattern, src_switch, dst_switch, symmetric)
                self.max_bandwidth_obj.append(max_bw_obj)

    # Translates the TE objectives to the `json_file`
    def to_json(self, json_file):
        json_dict = {
            'pass_by_paths': self.pass_by_paths_obj,
            'min_latency': self.min_latency_obj,
            'max_bandwidth': self.max_bandwidth_obj,
        }

        with open('%s' % json_file, 'w', encoding='utf-8') as f:
            json.dump(json_dict, f, ensure_ascii=False,
                      indent=4, cls=DefaultEncoder)

    # This function translates the objectives in `self.pass_by_paths_obj` to a list of Rules in `self.rules`
    # It should:
    #   call `self.calculate_rules_for_path` as needed
    #   handle traffic in reverse direction when `symmetric` is True
    #   call `self.send_openflow_rules()` at the end
    def provision_pass_by_paths(self):
        self.rules = []
        for obj in self.pass_by_paths_obj:
            rules = self.calculate_rules_for_path(
                obj.switches, obj.match_pattern, obj.symmetric)
            self.rules.extend(rules)
            if (obj.symmetric):
                rules_reverse = self.calculate_rules_for_path(
                    obj.switches[::-1], obj.match_pattern, obj.symmetric)
                self.rules.extend(rules_reverse)
        self.send_openflow_rules()

    # This function translates the objectives in `self.min_latency_obj` to a list of Rules in `self.rules`
    # It should:
    #   call `self.calculate_rules_for_path` as needed
    #   consider using the function `networkx.shortest_path` in the networkx package
    #   handle traffic in reverse direction when `symmetric` is True
    #   call `self.send_openflow_rules()` at the end

    def provision_min_latency_paths(self):
        self.rules = []
        for obj in self.min_latency_obj:
            src_str = str(obj.src_switch)
            dst_str = str(obj.dst_switch)
            path = nx.shortest_path(
                self.topo, src_str, dst_str, weight='delay')
            rules = self.calculate_rules_for_path(
                path, obj.match_pattern, obj.symmetric)
            self.rules.extend(rules)
            if (obj.symmetric):
                path_reverse = nx.shortest_path(
                    self.topo, dst_str, src_str, weight='delay')
                rules_reverse = self.calculate_rules_for_path(
                    path_reverse, obj.match_pattern, obj.symmetric)
                self.rules.extend(rules_reverse)
        self.send_openflow_rules()

    # BONUS:
    # This function translates the objectives in `self.max_bandwidth_obj` to a list of Rules in `self.rules`
    # It should:
    #   call `self.calculate_rules_for_path` as needed
    #   consider what algorithms to use (from networkx) to calculate the paths
    #   handle traffic in reverse direction when `symmetric` is True
    #   call `self.send_openflow_rules()` at the end
    def provision_max_bandwidth_paths(self):
        pass

    # BONUS: Used to react to changes in the network (the controller notifies the App)
    def on_notified(self, **kwargs):
        pass
