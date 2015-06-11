<script type="text/html" id="osf_storage_file_added">
added file
<a class="overflow log-file-link" data-bind="click: NodeActions.addonFileRedirect">
    {{ stripSlash(params.path) }}</a> to OSF Storage in
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}">{{ nodeTitle }}</a>
</script>

<script type="text/html" id="osf_storage_folder_created">
created folder
<span class="overflow log-folder">{{ stripSlash(params.path) }}</span> in
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}">{{ nodeTitle }}</a>
</script>

<script type="text/html" id="osf_storage_file_updated">
updated file
<a class="overflow log-file-link" data-bind="click: NodeActions.addonFileRedirect">
    {{ stripSlash(params.path) }}</a> to OSF Storage in
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}">{{ nodeTitle }}</a>
</script>

<script type="text/html" id="osf_storage_file_removed">
  removed {{ pathType(params.path) }} <span class="overflow">
      {{ stripSlash(params.path) }}</span> from OSF Storage in
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}">{{ nodeTitle }}</a>
</script>


## Legacy log templates for previous OSF Files
<script type="text/html" id="file_added">
added file <a class="overflow log-file-link" data-bind="click: NodeActions.addonFileRedirect, text: params.path"></a> to
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}, text: nodeTitle"></a>
</script>

<script type="text/html" id="file_updated">
updated file <a class="overflow log-file-link" data-bind="click: NodeActions.addonFileRedirect, text: params.path"></a> in
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}, text: nodeTitle"></a>
</script>

<script type="text/html" id="file_removed">
removed file <span data-bind="text: params.path"></span> from
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}, text: nodeTitle"></a>
</script>
