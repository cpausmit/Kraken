// Kraken monitoring dashboard -- vanilla JS, no build step. Polls status.json (written by
// bin/generateStatus.py, shipped to the web root by the existing rsync bridge) and re-renders
// in place, so the page feels live even though the underlying mechanism is periodic
// regeneration + rsync, not a persistent backend.
(function () {
  'use strict';

  var POLL_MS = 20000;
  var AGENT_NAMES = { catalogd: 'catalog creation log', cleanupd: 'cleanup logs',
                      monitord: 'monitor for cataloging', reviewd: 'request review logs' };

  function esc(s) {
    var d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
  }

  function bustImg(url) {
    return url + (url.indexOf('?') === -1 ? '?' : '&') + 't=' + Date.now();
  }

  function badge(health) {
    var h = health || 'unknown';
    return '<span class="badge badge-' + esc(h) + '">' + esc(h) + '</span>';
  }

  function fmtAge(age_s) {
    if (age_s === null || age_s === undefined || age_s < 0) return 'unknown';
    if (age_s < 120) return age_s + 's ago';
    if (age_s < 7200) return Math.round(age_s / 60) + 'm ago';
    return Math.round(age_s / 3600) + 'h ago';
  }

  function link(path, text) {
    return '<a href="detail.html?path=' + encodeURIComponent(path) + '">' + esc(text) + '</a>';
  }

  // no-op today: the single call site a future read/write "actions" layer would hook into
  // (e.g. resubmit/resync buttons keyed off node.id) without touching the render functions above.
  function renderActions(node) {
    return '';
  }

  function renderHeartbeat(tree) {
    var el = document.getElementById('heartbeat');
    if (!el) return;
    el.innerHTML = badge(tree.heartbeat.health) + ' heartbeat ' + esc(fmtAge(tree.heartbeat.age_s)) +
                   ' -- generated ' + esc(fmtAge(Math.round(Date.now() / 1000) - tree.generated_at));
  }

  function renderOverview(tree) {
    var out = document.getElementById('campaigns');
    if (!out) return;

    var html = '<pre>';
    var configs = Object.keys(tree.campaigns).sort();
    if (configs.length === 0) {
      html += '(no campaigns found)\n';
    }
    configs.forEach(function (config) {
      var versions = Object.keys(tree.campaigns[config]).sort();
      versions.forEach(function (version) {
        var v = tree.campaigns[config][version];
        html += badge(v.health) + ' ' + (v.active ? '(active) ' : '') +
                link(config + '/' + version, config + '/' + version) + '\n';
      });
    });
    html += '</pre>';
    out.innerHTML = html;

    var agentsOut = document.getElementById('agents');
    if (agentsOut) {
      var ahtml = '<pre>';
      Object.keys(AGENT_NAMES).forEach(function (name) {
        ahtml += '    <a href="detail.html?agent=' + encodeURIComponent(name) + '">' + esc(name) +
                 '</a> -- ' + esc(AGENT_NAMES[name]) + '\n';
      });
      ahtml += '</pre>';
      agentsOut.innerHTML = ahtml;
    }
  }

  function renderVersion(tree, config, version) {
    var v = tree.campaigns[config] && tree.campaigns[config][version];
    if (!v) return '<p>Unknown campaign/version: ' + esc(config) + '/' + esc(version) + '</p>';

    var html = '<h1>' + esc(config) + '/' + esc(version) + ' ' + badge(v.health) + '</h1>';
    html += '<p>' + Object.keys(v.pys).map(function (py) {
      return esc(py) + (v.pys[py] ? ' (active)' : '');
    }).join(', ') + '</p>';

    if (v.catalog_lag_s !== null && v.catalog_lag_s !== undefined) {
      html += '<p>catalog last write: ' + esc(fmtAge(v.catalog_lag_s)) + '</p>';
    }

    if (v.plots.length) {
      html += '<div class="plots">' + v.plots.map(function (p) {
        var url = 'reviewd/' + config + '/' + version + '/' + p;
        return '<a href="' + url + '"><img src="' + bustImg(url) + '"></a>';
      }).join('') + '</div>';
    }

    html += renderActions(v);

    html += '<h2>Samples</h2><table class="samples"><tr>' +
      '<th>Health</th><th>Dataset</th><th>Done/Total</th><th>NoCat</th>' +
      '<th>Batch</th><th>Idle</th><th>Run</th><th>Held</th></tr>';
    Object.keys(v.samples).sort().forEach(function (dataset) {
      var s = v.samples[dataset];
      html += '<tr><td>' + badge(s.health) + '</td>' +
        '<td>' + link(s.id, dataset) + '</td>' +
        '<td>' + s.n_done + '/' + s.n_total + '</td>' +
        '<td>' + s.n_nocatalog + '</td>' +
        '<td>' + s.n_batch + '</td><td>' + s.n_idle + '</td>' +
        '<td>' + s.n_running + '</td><td>' + s.n_held + '</td></tr>';
    });
    html += '</table>';

    html += '<h2>Raw logs</h2><ul>';
    v.status_files.concat(v.incomplete_files, v.queue_file).forEach(function (f) {
      var url = 'reviewd/' + config + '/' + version + '/' + f;
      html += '<li><a href="' + url + '">' + esc(f) + '</a></li>';
    });
    html += '</ul>';

    return html;
  }

  function renderSample(tree, config, version, dataset) {
    var v = tree.campaigns[config] && tree.campaigns[config][version];
    var s = v && v.samples[dataset];
    if (!s) return '<p>Unknown sample: ' + esc(config) + '/' + esc(version) + '/' + esc(dataset) + '</p>';

    var base = 'reviewd/' + config + '/' + version + '/' + dataset + '/';
    var html = '<h1>' + link(config + '/' + version, config + '/' + version) + ' / ' +
               esc(dataset) + ' ' + badge(s.health) + '</h1>';
    html += '<p>' + s.n_done + '/' + s.n_total + ' done, ' + s.n_nocatalog + ' not yet catalogued -- ' +
            'batch ' + s.n_batch + ', idle ' + s.n_idle + ', running ' + s.n_running + ', held ' + s.n_held + '</p>';

    html += renderActions(s);

    if (s.plots.length) {
      html += '<div class="plots">' + s.plots.map(function (p) {
        var url = base + p;
        return '<a href="' + url + '"><img src="' + bustImg(url) + '"></a>';
      }).join('') + '</div>';
    }

    html += '<p>';
    s.readme.concat(s.ncounts_err).forEach(function (f) {
      html += '<a href="' + base + f + '">' + esc(f) + '</a> ';
    });
    html += '</p>';

    return html;
  }

  function renderAgent(tree, name) {
    var a = tree.agents[name];
    if (!a) return '<p>Unknown agent: ' + esc(name) + '</p>';

    var html = '<h1>' + esc(name) + ' agent</h1>';
    if (a.plots.length) {
      html += '<h2>Plots</h2><div class="plots">' + a.plots.map(function (p) {
        var url = name + '/' + p;
        return '<a href="' + url + '"><img src="' + bustImg(url) + '"></a>';
      }).join('') + '</div>';
    }
    html += '<h2>Logfiles</h2><ul>';
    a.logs.forEach(function (l) {
      html += '<li><a href="' + name + '/' + l + '">' + esc(l) + '</a></li>';
    });
    html += '</ul>';

    return html;
  }

  function renderDetail(tree) {
    var out = document.getElementById('content');
    if (!out) return;

    var params = new URLSearchParams(window.location.search);
    var agent = params.get('agent');
    var path = params.get('path');

    if (agent) {
      out.innerHTML = renderAgent(tree, agent);
      return;
    }
    if (!path) {
      out.innerHTML = '<p>No path given.</p>';
      return;
    }

    var f = path.split('/');
    if (f.length === 2) {
      out.innerHTML = renderVersion(tree, f[0], f[1]);
    } else if (f.length === 3) {
      out.innerHTML = renderSample(tree, f[0], f[1], f[2]);
    } else {
      out.innerHTML = '<p>Malformed path: ' + esc(path) + '</p>';
    }
  }

  function refresh() {
    fetch('status.json', { cache: 'no-store' }).then(function (r) {
      return r.json();
    }).then(function (tree) {
      renderHeartbeat(tree);
      renderOverview(tree);
      renderDetail(tree);
    }).catch(function (ex) {
      console.error('status.json fetch failed', ex);
    });
  }

  refresh();
  setInterval(refresh, POLL_MS);
})();
