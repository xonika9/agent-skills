#!/usr/bin/env python3
"""Strict YAML inspection shared by OKF migration scripts."""

from __future__ import annotations

import json
import subprocess

RUBY_INSPECT = r'''
require "yaml"; require "json"; require "time"

def inspect_node(node, path, duplicates)
  case node
  when Psych::Nodes::Mapping
    seen = {}
    node.children.each_slice(2) do |key, value|
      unless key.is_a?(Psych::Nodes::Scalar)
        raise "complex mapping keys are not supported"
      end
      name = key.value
      location = (path + [name]).join(".")
      duplicates << location if seen[name]
      seen[name] = true
      inspect_node(value, path + [name], duplicates)
    end
  when Psych::Nodes::Sequence
    node.children.each_with_index do |child, index|
      inspect_node(child, path + [index.to_s], duplicates)
    end
  end
end

begin
  source = STDIN.read
  stream = Psych.parse_stream(source)
  root = stream.children.first&.root
  duplicates = []
  inspect_node(root, [], duplicates)
  raise "duplicate key(s): #{duplicates.uniq.join(', ')}" unless duplicates.empty?
  top_keys = []
  top_scalars = {}
  if root.is_a?(Psych::Nodes::Mapping)
    root.children.each_slice(2) do |key, value_node|
      top_keys << {"key" => key.value, "line" => key.start_line}
      top_scalars[key.value] = value_node.value if value_node.is_a?(Psych::Nodes::Scalar)
    end
  end
  value = YAML.safe_load(source, permitted_classes: [Time], permitted_symbols: [], aliases: false)
  STDOUT.write(JSON.generate({"ok" => true, "value" => value, "top_keys" => top_keys, "top_scalars" => top_scalars}))
rescue => e
  STDOUT.write(JSON.generate({"ok" => false, "error" => e.message})); exit 1
end
'''


def inspect_yaml(header: str):
    try:
        proc = subprocess.run(
            ["ruby", "-e", RUBY_INSPECT], input=header, text=True,
            capture_output=True, check=False,
        )
    except FileNotFoundError:
        return None, "Ruby/Psych is required for strict YAML validation"
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None, "strict YAML parser returned invalid output"
    if not result.get("ok"):
        return None, f"invalid YAML: {result.get('error', 'unknown error')}"
    if not isinstance(result.get("value"), dict):
        return None, "frontmatter must be a mapping"
    return result, None
