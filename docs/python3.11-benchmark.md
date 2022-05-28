# Using `joe-qoi` to benchmark Python 3.11

One of the goals for the Python 3.11 release is an increase in performance of the Python
interpreter. `joe-qoi` is a pure-Python implementation of a low-level image format, and
the performance of `joe-qoi` is strongly CPU-bound. With that in mind, I thought that
`joe-qoi` would be a good opportunity to try out the latest Python 3.11 pre-release, and
compare performance against previous Python releases.

## Approach

I ran these tests on my (very old, very slow) home network server, as despite it's age
and low power, it is significantly faster than my Raspberry Pi 2B. The server is running
Ubuntu Server 20.04 LTS, and writing this up gave me a good excuse to learn how to get
machine hardware information on Linux.

For reference, more to myself than anyone else, some commands of interest:
```bash
# Get CPU name, architecture, number of cores
cat /proc/cpuinfo
# Get memory information
sudo lshw -c memory
# Operating system info
cat /etc/*release
```

| | |
| - | - |
| CPU | AMD Athlon(tm) II Neo N36L |
| Cores | 2 |
| Clock speed | 800 MHz |
| RAM | 3GiB DIMM with ecc |
| Python 3.8 | 3.8.3 (system) |
| Python 3.9 | 3.9.1 |
| Python 3.10 | 3.10.4 |
| Python 3.11 | 3.11.0b1 |

Each non-system Python (i.e. all but 3.8) were built on-machine from source, using
profiler guided optimizations and link time optimization. i.e.

```bash
./configure --enable-optimizations --with-lto
```

### Running the benchmarks

Really, nothing terribly complicated. I'm sure there are far better and more
statistically reliable ways to calculate this information, but it took about 5 minutes
of interaction and almost no effort to implement and analyze. The process was, for each
Python interpreter:

1. Create a virtual environment (i.e. `python3.9 -m venv venv3.9; source ./venv3.9/bin/activate.fish`)
1. Set up the dependencies (`pip install -r requirements-dev.txt`)
    - Python 3.11 was slightly more complex because there isn't a Pillow wheel available
    yet. I had to `sudo apt install -y libjpeg-dev`)
1. Run the pytest tests with `--run-slow` and write the results to a benchmarks directory

```fish
mkdir bench
for ver in "3.8" "3.9" "3.10 "3.11"
    source venv$ver/bin/activate.fish
    for ix in (seq 0 9)
        python -m pytest test > "./bench/python_"$ver"_"$ix".txt"
    end
    deactivate
end
```

## Results

Some of the discussion about Python 3.11 noted that the interpreter might be "about 20%
 faster". This is heavily caveated in that there will likely be little to no speedup in
libraries that are calling `C` (or other compiled language) libraries under the hood.

With `joe-qoi`'s pure-Python implementation, however, this speedup was indeed delivered
on.

## Analyzing the data

This could obviously be done entirely in Python, but took a couple seconds in the shell
to get the information I needed

```sh
grep -P -o '\d+\.\d{2}s' ./bench/*.txt | sed 's/:/,/g' > ./bench/rollup.csv
```

Then in an IPython REPL, after copying the file contents to clipboard (my local machine
has the full Anaconda stack, file server does not):

```python
import pandas as pd
import plotly.express as px

df = pd.read_clipboard(sep=",", names=["filename", "run_time"])
df["Python Version"] = df.filename.apply(lambda x: x.split("_")[1])
df["Seconds"] = df.run_time.apply(lambda x: float(x[:-1]))

# Use system Python as a baseline
three_eight_median = df[df["Python Version"] == "3.8"]["Seconds"].median()
df["Ratio"] = df["Seconds"] / three_eight_median
med = df.groupby("Python Version").median()

fig = px.box(
    df,
    y="Python Version",
    x="Seconds",
    points="all",
    title="Execution time of 'joe-qoi' test suite"
)
with open("benchmark.html", "w") as hdl:
    hdl.write(fig.to_html(include_plotlyjs="cdn"))
```

Contents of the `med` DataFrame:
```
                Seconds     Ratio
Python Version
3.10            204.430  1.029615
3.11            167.675  0.844498
3.8             198.550  1.000000
3.9             208.290  1.049056
```

## Hopefully this works

Let's see if I can just embed the `<div>` directly in GitHub Pages

<div>
        <script type="text/javascript">window.PlotlyConfig = { MathJaxConfig: 'local' };</script>
        <script src="https://cdn.plot.ly/plotly-2.2.0.min.js"></script>
        <div id="6131e1a2-860b-4826-8c26-9b596a7efec3" class="plotly-graph-div" style="height:100%; width:100%;"></div>
        <script
            type="text/javascript">                                    window.PLOTLYENV = window.PLOTLYENV || {}; if (document.getElementById("6131e1a2-860b-4826-8c26-9b596a7efec3")) { Plotly.newPlot("6131e1a2-860b-4826-8c26-9b596a7efec3", [{ "alignmentgroup": "True", "boxpoints": "all", "hovertemplate": "Seconds=%{x}<br>Python Version=%{y}<extra></extra>", "legendgroup": "", "marker": { "color": "#636efa" }, "name": "", "notched": false, "offsetgroup": "", "orientation": "h", "showlegend": false, "type": "box", "x": [196.24, 201.31, 197.77, 197.58, 200.24, 195.77, 199.73, 196.11, 199.33, 201.98, 206.32, 207.41, 206.39, 207.21, 211.43, 216.79, 210.2, 209.17, 215.86, 205.36, 203.33, 217.95, 205.76, 202.42, 202.16, 206.81, 206.18, 205.53, 201.38, 200.28, 166.98, 168.77, 171.06, 167.81, 165.44, 167.86, 166.61, 165.56, 169.77, 167.54], "x0": " ", "xaxis": "x", "y": ["3.8", "3.8", "3.8", "3.8", "3.8", "3.8", "3.8", "3.8", "3.8", "3.8", "3.9", "3.9", "3.9", "3.9", "3.9", "3.9", "3.9", "3.9", "3.9", "3.9", "3.10", "3.10", "3.10", "3.10", "3.10", "3.10", "3.10", "3.10", "3.10", "3.10", "3.11", "3.11", "3.11", "3.11", "3.11", "3.11", "3.11", "3.11", "3.11", "3.11"], "y0": " ", "yaxis": "y" }], { "boxmode": "group", "legend": { "tracegroupgap": 0 }, "template": { "data": { "bar": [{ "error_x": { "color": "#2a3f5f" }, "error_y": { "color": "#2a3f5f" }, "marker": { "line": { "color": "#E5ECF6", "width": 0.5 }, "pattern": { "fillmode": "overlay", "size": 10, "solidity": 0.2 } }, "type": "bar" }], "barpolar": [{ "marker": { "line": { "color": "#E5ECF6", "width": 0.5 }, "pattern": { "fillmode": "overlay", "size": 10, "solidity": 0.2 } }, "type": "barpolar" }], "carpet": [{ "aaxis": { "endlinecolor": "#2a3f5f", "gridcolor": "white", "linecolor": "white", "minorgridcolor": "white", "startlinecolor": "#2a3f5f" }, "baxis": { "endlinecolor": "#2a3f5f", "gridcolor": "white", "linecolor": "white", "minorgridcolor": "white", "startlinecolor": "#2a3f5f" }, "type": "carpet" }], "choropleth": [{ "colorbar": { "outlinewidth": 0, "ticks": "" }, "type": "choropleth" }], "contour": [{ "colorbar": { "outlinewidth": 0, "ticks": "" }, "colorscale": [[0.0, "#0d0887"], [0.1111111111111111, "#46039f"], [0.2222222222222222, "#7201a8"], [0.3333333333333333, "#9c179e"], [0.4444444444444444, "#bd3786"], [0.5555555555555556, "#d8576b"], [0.6666666666666666, "#ed7953"], [0.7777777777777778, "#fb9f3a"], [0.8888888888888888, "#fdca26"], [1.0, "#f0f921"]], "type": "contour" }], "contourcarpet": [{ "colorbar": { "outlinewidth": 0, "ticks": "" }, "type": "contourcarpet" }], "heatmap": [{ "colorbar": { "outlinewidth": 0, "ticks": "" }, "colorscale": [[0.0, "#0d0887"], [0.1111111111111111, "#46039f"], [0.2222222222222222, "#7201a8"], [0.3333333333333333, "#9c179e"], [0.4444444444444444, "#bd3786"], [0.5555555555555556, "#d8576b"], [0.6666666666666666, "#ed7953"], [0.7777777777777778, "#fb9f3a"], [0.8888888888888888, "#fdca26"], [1.0, "#f0f921"]], "type": "heatmap" }], "heatmapgl": [{ "colorbar": { "outlinewidth": 0, "ticks": "" }, "colorscale": [[0.0, "#0d0887"], [0.1111111111111111, "#46039f"], [0.2222222222222222, "#7201a8"], [0.3333333333333333, "#9c179e"], [0.4444444444444444, "#bd3786"], [0.5555555555555556, "#d8576b"], [0.6666666666666666, "#ed7953"], [0.7777777777777778, "#fb9f3a"], [0.8888888888888888, "#fdca26"], [1.0, "#f0f921"]], "type": "heatmapgl" }], "histogram": [{ "marker": { "pattern": { "fillmode": "overlay", "size": 10, "solidity": 0.2 } }, "type": "histogram" }], "histogram2d": [{ "colorbar": { "outlinewidth": 0, "ticks": "" }, "colorscale": [[0.0, "#0d0887"], [0.1111111111111111, "#46039f"], [0.2222222222222222, "#7201a8"], [0.3333333333333333, "#9c179e"], [0.4444444444444444, "#bd3786"], [0.5555555555555556, "#d8576b"], [0.6666666666666666, "#ed7953"], [0.7777777777777778, "#fb9f3a"], [0.8888888888888888, "#fdca26"], [1.0, "#f0f921"]], "type": "histogram2d" }], "histogram2dcontour": [{ "colorbar": { "outlinewidth": 0, "ticks": "" }, "colorscale": [[0.0, "#0d0887"], [0.1111111111111111, "#46039f"], [0.2222222222222222, "#7201a8"], [0.3333333333333333, "#9c179e"], [0.4444444444444444, "#bd3786"], [0.5555555555555556, "#d8576b"], [0.6666666666666666, "#ed7953"], [0.7777777777777778, "#fb9f3a"], [0.8888888888888888, "#fdca26"], [1.0, "#f0f921"]], "type": "histogram2dcontour" }], "mesh3d": [{ "colorbar": { "outlinewidth": 0, "ticks": "" }, "type": "mesh3d" }], "parcoords": [{ "line": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "type": "parcoords" }], "pie": [{ "automargin": true, "type": "pie" }], "scatter": [{ "marker": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "type": "scatter" }], "scatter3d": [{ "line": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "marker": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "type": "scatter3d" }], "scattercarpet": [{ "marker": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "type": "scattercarpet" }], "scattergeo": [{ "marker": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "type": "scattergeo" }], "scattergl": [{ "marker": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "type": "scattergl" }], "scattermapbox": [{ "marker": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "type": "scattermapbox" }], "scatterpolar": [{ "marker": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "type": "scatterpolar" }], "scatterpolargl": [{ "marker": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "type": "scatterpolargl" }], "scatterternary": [{ "marker": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "type": "scatterternary" }], "surface": [{ "colorbar": { "outlinewidth": 0, "ticks": "" }, "colorscale": [[0.0, "#0d0887"], [0.1111111111111111, "#46039f"], [0.2222222222222222, "#7201a8"], [0.3333333333333333, "#9c179e"], [0.4444444444444444, "#bd3786"], [0.5555555555555556, "#d8576b"], [0.6666666666666666, "#ed7953"], [0.7777777777777778, "#fb9f3a"], [0.8888888888888888, "#fdca26"], [1.0, "#f0f921"]], "type": "surface" }], "table": [{ "cells": { "fill": { "color": "#EBF0F8" }, "line": { "color": "white" } }, "header": { "fill": { "color": "#C8D4E3" }, "line": { "color": "white" } }, "type": "table" }] }, "layout": { "annotationdefaults": { "arrowcolor": "#2a3f5f", "arrowhead": 0, "arrowwidth": 1 }, "autotypenumbers": "strict", "coloraxis": { "colorbar": { "outlinewidth": 0, "ticks": "" } }, "colorscale": { "diverging": [[0, "#8e0152"], [0.1, "#c51b7d"], [0.2, "#de77ae"], [0.3, "#f1b6da"], [0.4, "#fde0ef"], [0.5, "#f7f7f7"], [0.6, "#e6f5d0"], [0.7, "#b8e186"], [0.8, "#7fbc41"], [0.9, "#4d9221"], [1, "#276419"]], "sequential": [[0.0, "#0d0887"], [0.1111111111111111, "#46039f"], [0.2222222222222222, "#7201a8"], [0.3333333333333333, "#9c179e"], [0.4444444444444444, "#bd3786"], [0.5555555555555556, "#d8576b"], [0.6666666666666666, "#ed7953"], [0.7777777777777778, "#fb9f3a"], [0.8888888888888888, "#fdca26"], [1.0, "#f0f921"]], "sequentialminus": [[0.0, "#0d0887"], [0.1111111111111111, "#46039f"], [0.2222222222222222, "#7201a8"], [0.3333333333333333, "#9c179e"], [0.4444444444444444, "#bd3786"], [0.5555555555555556, "#d8576b"], [0.6666666666666666, "#ed7953"], [0.7777777777777778, "#fb9f3a"], [0.8888888888888888, "#fdca26"], [1.0, "#f0f921"]] }, "colorway": ["#636efa", "#EF553B", "#00cc96", "#ab63fa", "#FFA15A", "#19d3f3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"], "font": { "color": "#2a3f5f" }, "geo": { "bgcolor": "white", "lakecolor": "white", "landcolor": "#E5ECF6", "showlakes": true, "showland": true, "subunitcolor": "white" }, "hoverlabel": { "align": "left" }, "hovermode": "closest", "mapbox": { "style": "light" }, "paper_bgcolor": "white", "plot_bgcolor": "#E5ECF6", "polar": { "angularaxis": { "gridcolor": "white", "linecolor": "white", "ticks": "" }, "bgcolor": "#E5ECF6", "radialaxis": { "gridcolor": "white", "linecolor": "white", "ticks": "" } }, "scene": { "xaxis": { "backgroundcolor": "#E5ECF6", "gridcolor": "white", "gridwidth": 2, "linecolor": "white", "showbackground": true, "ticks": "", "zerolinecolor": "white" }, "yaxis": { "backgroundcolor": "#E5ECF6", "gridcolor": "white", "gridwidth": 2, "linecolor": "white", "showbackground": true, "ticks": "", "zerolinecolor": "white" }, "zaxis": { "backgroundcolor": "#E5ECF6", "gridcolor": "white", "gridwidth": 2, "linecolor": "white", "showbackground": true, "ticks": "", "zerolinecolor": "white" } }, "shapedefaults": { "line": { "color": "#2a3f5f" } }, "ternary": { "aaxis": { "gridcolor": "white", "linecolor": "white", "ticks": "" }, "baxis": { "gridcolor": "white", "linecolor": "white", "ticks": "" }, "bgcolor": "#E5ECF6", "caxis": { "gridcolor": "white", "linecolor": "white", "ticks": "" } }, "title": { "x": 0.05 }, "xaxis": { "automargin": true, "gridcolor": "white", "linecolor": "white", "ticks": "", "title": { "standoff": 15 }, "zerolinecolor": "white", "zerolinewidth": 2 }, "yaxis": { "automargin": true, "gridcolor": "white", "linecolor": "white", "ticks": "", "title": { "standoff": 15 }, "zerolinecolor": "white", "zerolinewidth": 2 } } }, "title": { "text": "Execution time of 'joe-qoi' test suite" }, "xaxis": { "anchor": "y", "domain": [0.0, 1.0], "title": { "text": "Seconds" } }, "yaxis": { "anchor": "x", "domain": [0.0, 1.0], "title": { "text": "Python Version" } } }, { "responsive": true }) };                            </script>
</div>
