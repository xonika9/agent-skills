# Locate

Find where one named metric goes. A worker reads and measures, then returns a breakdown with evidence labels and the path to its raw data.

## Start cheap

First scan the code on the scenario's path for the waste listed in [audit](audit.md#what-counts-as-bad) and label it `code`. Then measure, biggest candidate first. Locating is done when the main cause's share of the metric is measured and the rest is labeled; build the full breakdown below only when no single cause explains the minimum gain.

## Time of one operation

Take start and end from the side of whoever waits. If the data ends earlier, such as at a server event rather than visible output, the missing stretch is a `NOT_PROVEN` segment.

Build the critical path from logs, traces, and browser traces as non-overlapping segments. A segment counts only with evidence that the next event waits for it — a code path, log ordering, or protocol; otherwise it is background and is not added. Close silent gaps with temporary timing marks. A lever's bound is the time it removes from the critical path, which can be less than the segment it shortens.

Work that does not depend on the request can move earlier: into an image or snapshot, pre-started instances, connection pools, warmed caches, a start on the first sign of intent, or binding a prepared resource to the request late. Name what makes the prepared result reusable — version, credentials, freshness, isolation — and measure the wait both when it is ready and when it is not.

Overhead that may belong to the test environment, such as nested virtualization or a weak machine, is checked on a production-like machine; without one, the bound is `NOT_PROVEN` with the direction in which it may be wrong.

## Under load

Choose the load model from the real traffic: independent arrivals become a fixed arrival rate raised in steps; a fixed set of users or workers becomes that many concurrent clients. Confirm the load generator is not the limit. Per step, record the end metric with its sample count and only the data the current hypothesis needs. A saturated resource or a growing queue is a candidate until changing that limit changes the result as predicted. Remove work at the limit before adding capacity. Write thresholds into the load script so the run can fail, and check the script before a full run.

## Memory

Warm up, repeat one action N times, return to rest, and compare snapshots; report growth per repetition and what holds the memory. A bounded cache is not a leak.

## CPU

Profile under realistic load. If waiting dominates, go back to time of one operation. For a hot function, find why it is called so often before why each call is slow.

## Size

A size limit the owner names is a metric in itself. Without one, tie size to the time or money it costs.

## Money

Split the bill by source — service, route, job, and model calls as calls × tokens × price, with prices from the provider's current price list or the bill — and compute the cost per unit of work, such as a request or a conversation. When a speed-up costs money, such as idle capacity, show both sides.

## Done

The main cause's share of the metric is measured, the rest is labeled, and each proposed lever has a bound.
