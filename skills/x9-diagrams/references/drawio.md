# draw.io native XML and rendering

Use this adapter for native, editable `.drawio` files. diagrams.net also accepts several embedded or compressed forms, but uncompressed XML is the reviewable default unless the target requires another form.

Current mechanics belong to the official [file-format guide](https://www.drawio.com/docs/manual/editor/save-file-formats/), [XML export guide](https://www.drawio.com/docs/manual/export/export-to-xml/), [diagram-generation reference](https://www.drawio.com/docs/reference/diagram-generation/), and compatible diagrams.net editor or desktop application. Verify load-bearing behavior there instead of relying on a community skill.

## Native envelope

A directly authored file uses this hierarchy:

```xml
<mxfile>
  <diagram id="page-id" name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- vertices and edges -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Each page has one `diagram`. Within its graph, cell `0` is the root and cell `1` is the default layer. Keep every ID unique within that page's graph; root IDs may repeat on another page. XML-escape labels and attribute values.

## Cells and geometry

A normal vertex is an `mxCell` with `vertex="1"`, a valid parent, a style string, and child `mxGeometry` with `as="geometry"`:

```xml
<mxCell id="api" value="API" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
  <mxGeometry x="320" y="120" width="160" height="64" as="geometry"/>
</mxCell>
```

An edge uses `edge="1"`, valid `source` and `target` IDs, and relative edge geometry:

```xml
<mxCell id="user-api" value="HTTPS" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;" edge="1" parent="1" source="user" target="api">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

Use explicit coordinates when placement carries meaning. Keep peers aligned, leave routing gutters, and add waypoints only when automatic routing crosses unrelated content. Do not position edge labels as unrelated vertices.

## Pages, layers, and containers

- Use pages for distinct views, scenarios, or stable detail levels.
- Represent each layer as an `mxCell` under root `0`; place its visible cells under that layer.
- Use a container only when ownership, scope, trust, deployment, or movement as one unit matters.
- For child geometry relative to a container, preserve the parent ID and the coordinate convention expected by that shape; verify movement and resize behavior in the editor.
- Keep boundaries behind their children and edges behind labels where the editor's paint order follows cell order.

Prefer built-in shapes when simple geometry communicates the role. Use library stencils only when the audience needs that visual vocabulary and the target editor has the library. Do not substitute a vendor icon for a textual identity the viewer must understand.

## Styling

Styles are semicolon-delimited `key=value` pairs. Apply one role consistently and end style strings with a semicolon. Keep important meaning redundant with a label, shape, or line pattern rather than color alone. Preserve the user's existing theme during edits unless the task includes restyling.

Do not treat arbitrary community CLI flags, page indexes, or export claims as stable. Inspect the actual installed tool's help and official documentation first.

## Validation

Validate in layers:

1. XML parses without recovery.
2. The file contains `mxfile`, at least one `diagram`, `mxGraphModel`, `root`, and root cells `0` and `1`.
3. IDs are unique; every parent, source, and target resolves; vertices and edges have appropriate geometry.
4. A compatible diagrams.net editor opens the native file without repair or data loss.
5. The editor or compatible exporter renders it; inspect the output at whole-view and normal editing scale.
6. Reopen the saved file when editability, page/layer preservation, or container behavior is load-bearing.

Do not delete the native source after export. A PNG, SVG, or PDF is delivery evidence or a companion, not a substitute for a requested editable `.drawio` file. If only steps 1–3 are possible, report `DEGRADED`; structural XML validation is not visual proof.
