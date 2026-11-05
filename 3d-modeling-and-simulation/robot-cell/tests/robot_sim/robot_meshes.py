"""TM5-900 link meshes for sim_view.html: Techman's own visual meshes, one GLB node per link (link_0..link_6).

    python robot_cell/tests/robot_sim/robot_meshes.py         (shared venv: trimesh; needs the internet once)

Source: Techman Robot's ROS driver, github.com/TechmanRobotInc/tmr_ros1 (branch noetic),
tm_description/meshes/tm5-900/visual/*.obj - the meshes tm5-900-nominal.urdf hangs on its links, each in
its link's own frame (the frames tm5_kin.py and sim_view.html build), in metres. Here: scaled to mm, merged
vertices, written to tm5_links.glb. Nothing is taken from RoboDK.
"""
import io
import urllib.request
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
URL = "https://raw.githubusercontent.com/TechmanRobotInc/tmr_ros1/noetic/tm_description/meshes/tm5-900/visual/"
LINKS = ["tm5-base", "tmr_400w_01", "tm5-900_arm1", "tm5-900_arm2", "tmr_100w_01", "tmr_100w_02", "tmr_ee"]
COLOURS = [(0.93, 0.93, 0.92, 1), (0.93, 0.93, 0.92, 1), (0.93, 0.93, 0.92, 1), (0.93, 0.93, 0.92, 1),
           (0.93, 0.93, 0.92, 1), (0.93, 0.93, 0.92, 1), (0.35, 0.36, 0.38, 1)]


def main():
    scene = trimesh.Scene()
    for i, (name, colour) in enumerate(zip(LINKS, COLOURS)):
        with urllib.request.urlopen(URL + name + ".obj") as r:
            mesh = trimesh.load(io.BytesIO(r.read()), file_type="obj", force="mesh", process=True)
        mesh.apply_scale(1000)
        mesh.merge_vertices()
        mesh.visual = trimesh.visual.TextureVisuals(
            material=trimesh.visual.material.PBRMaterial(baseColorFactor=colour, metallicFactor=0.1, roughnessFactor=0.5))
        scene.add_geometry(mesh, node_name=f"link_{i}", geom_name=f"link_{i}")
        print(f"link_{i} {name}: {len(mesh.faces)} faces")
    out = HERE / "tm5_links.glb"
    out.write_bytes(scene.export(file_type="glb"))
    print(f"-> {out.name} {out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
