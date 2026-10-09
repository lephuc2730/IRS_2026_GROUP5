# Lab 06 Completion Checklist

| Lab step | Status | Evidence |
|---|---|---|
| Add nav_launch.py, Nav2 YAML and RViz config | DONE | Files are in launch/, config/ and rviz/. |
| Create map/ folder and add Week 6 .pgm/.yaml | DONE | Both map files are stored in hand_solo_virtual_nav/map/. |
| Install map resources from setup.py | DONE | setup.py contains the map glob. |
| Correct scan, odom, base and odom frames | DONE | Uses the live virtual Hand Solo topics/frames verified in Week 6. |
| Verify nav_launch.py paths | DONE | Package builds and launch succeeds. |
| Build and source package | DONE | Built in official ROS2 Jazzy workspace. |
| Open HMI and set Autonomous Mode | DONE | Real HMI capture shows Autonomous Mode green. |
| Launch nav_launch.py | DONE | All Nav2 lifecycle nodes became active. |
| Send autonomous navigation goal | DONE | NavigateToPose returned SUCCEEDED, error_code 0. |
| Install/register hs_waypoint_follower | DONE | ROS2 executable is present. |
| Add multiple waypoint route | DONE | Four-goal patrol route implemented. |
| Add Python time delays | DONE | 3-second waits occur between successful goals. |
| Run waypoint follower | DONE | All four goals succeeded in the official simulation. |
| Save runtime proof | DONE | GitHub Actions run 37935082673 and Week 7 evidence document. |

## Note on RViz input tools

The final runtime validated the same Nav2 interfaces used by the RViz Nav2 Goal and Publish Point tools. The autonomous goal itself was sent programmatically through the `NavigateToPose` action so its success/result could be captured deterministically in CI. The custom waypoint node then used that same Nav2 action interface for the four-goal patrol.
