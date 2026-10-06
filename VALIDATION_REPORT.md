# Static validation report

Validation performed without a ROS2/Ubuntu runtime:

- Python syntax compilation: **PASS**
  - Week 5 publisher, listener and probe
  - Week 6 starter node
  - Week 6 mapping launch file
  - both `setup.py` files
- `package.xml` XML parsing: **PASS** for both ROS2 packages
- `pa_slam_params.yaml` YAML parsing: **PASS**
- Week 5 and Week 6 portfolio source text is included under `docs/`

## Not runtime-validated

The following require the University ROS2 Jazzy/Docker simulation and are not claimed as completed runtime results:

- final Robot HMI status-message screenshot
- exact PLC JSON topic confirmation
- live `rqt_graph`
- live Week 6 `rqt_tf_tree`
- live RViz mapping screenshot
- `pa_warehouse_map_01.pgm` and `pa_warehouse_map_01.yaml`

This distinction is intentional so the repository does not contain fabricated experimental evidence.
