
%rebase layout globals(), js=['timeline/js/timeline.js'], css=['timeline/css/timeline.css']

<div id="timeline"></div>

<script>
  $(document).ready(function() {
  timeline = new VMM.Timeline();
  timeline.init("/static/timeline/js/houston.json");
  });
</script>
