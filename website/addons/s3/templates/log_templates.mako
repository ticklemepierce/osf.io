<script type="text/html" id="s3_file_added">
added file
<a class="overflow log-file-link" data-bind="click: NodeActions.addonFileRedirect, text: params.path"></a> to
bucket
<span data-bind="text: params.bucket"></span> in
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}, text: nodeTitle"></a>
</script>

<script type="text/html" id="s3_folder_created">
created folder
<span class="overflow log-folder">{{ stripSlash(params.path) }}</span> in
bucket {{ params.bucket }} in 
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}">{{ nodeTitle }}</a>
</script>

<script type="text/html" id="s3_file_updated">
updated file
<a class="overflow log-file-link" data-bind="click: NodeActions.addonFileRedirect, text: params.path"></a> in
bucket
<span data-bind="text: params.bucket"></span> in
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}, text: nodeTitle"></a>
</script>

<script type="text/html" id="s3_file_removed">
removed {{ pathType(params.path) }} <span class="overflow">{{ stripSlash(params.path) }}</span> from
bucket
<span data-bind="text: params.bucket"></span> in
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}, text: nodeTitle"></a>
</script>

<script type="text/html" id="s3_bucket_linked">
linked the Amazon S3 bucket /
<span data-bind="text: params.bucket"></span> to
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}, text: nodeTitle"></a>
</script>

<script type="text/html" id="s3_bucket_unlinked">
un-selected bucket
<span data-bind="text: params.bucket"></span> in
<a class="log-node-title-link overflow" data-bind="attr: {href: nodeUrl}, text: nodeTitle"></a>
</script>

<script type="text/html" id="s3_node_authorized">
authorized the Amazon S3 addon for 
<a class="log-node-title-link overflow"
    data-bind="attr: {href: nodeUrl}">{{ nodeTitle }}</a>
</script>

<script type="text/html" id="s3_node_deauthorized">
deauthorized the Amazon S3 addon for 
<a class="log-node-title-link overflow"
    data-bind="attr: {href: nodeUrl}">{{ nodeTitle }}</a>
</script>
