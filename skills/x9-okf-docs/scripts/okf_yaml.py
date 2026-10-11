#!/usr/bin/env python3
"""Strict YAML inspection shared by the OKF scripts; one Ruby process reads many headers."""

from __future__ import annotations

import json
import subprocess

RUBY_INSPECT = r'''
require "yaml"; require "json"; require "date"; require "time"

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

def json_value(value)
  case value
  when Time, Date
    value.iso8601
  when Symbol
    ":" + value.to_s
  when Hash
    value.transform_values { |item| json_value(item) }
  when Array
    value.map { |item| json_value(item) }
  else
    value
  end
end

def inspect_one(source)
  stream = Psych.parse_stream(source)
  root = stream.children.first&.root
  return {"ok" => true, "value" => {}, "top_keys" => [], "block" => true} if root.nil?
  duplicates = []
  inspect_node(root, [], duplicates)
  raise "duplicate key(s): #{duplicates.uniq.join(', ')}" unless duplicates.empty?
  top_keys = []
  block = true
  if root.is_a?(Psych::Nodes::Mapping)
    block = root.style == Psych::Nodes::Mapping::BLOCK
    root.children.each_slice(2) do |key, _|
      top_keys << {"key" => key.value, "line" => key.start_line}
    end
  end
  value = json_value(YAML.safe_load(source, permitted_classes: [Time, Date, Symbol], aliases: false))
  {"ok" => true, "value" => value, "top_keys" => top_keys, "block" => block}
rescue Exception => e
  {"ok" => false, "error" => e.message.to_s.lines.first.to_s.strip}
end

STDOUT.write(JSON.generate(JSON.parse(STDIN.read).map { |source| inspect_one(source) }))
'''

FLOW_COLON_HINT = (
    "; this YAML library cannot read an unquoted value containing ':' inside { } or [ ], "
    "so quote that value"
)


def inspect_many(headers):
    """Return (result, error) for each header text."""
    if not headers:
        return []
    try:
        proc = subprocess.run(
            ["ruby", "-e", RUBY_INSPECT], input=json.dumps(list(headers)), text=True,
            capture_output=True, check=False,
        )
    except FileNotFoundError:
        return [(None, "Ruby with Psych is required to read YAML frontmatter")] * len(headers)
    try:
        results = json.loads(proc.stdout)
    except json.JSONDecodeError:
        detail = proc.stderr.strip().splitlines()[-1:] or ["no output"]
        return [(None, f"the YAML reader failed: {detail[0]}")] * len(headers)
    output = []
    for result in results:
        if not result.get("ok"):
            error = result.get("error", "unknown error")
            if "unexpected ':'" in error:
                error += FLOW_COLON_HINT
            output.append((None, f"invalid YAML: {error}"))
        elif not isinstance(result.get("value"), dict):
            output.append((None, "frontmatter must be a mapping"))
        else:
            output.append((result, None))
    return output


def inspect_yaml(header: str):
    return inspect_many([header])[0]
