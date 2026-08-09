from novels.postprocess_common.cleanup_empty_lines import cleanup_empty_lines
from novels.tasks.syosetu_org.process.cleanup_html import cleanup_html


test = """


"""

delined = cleanup_empty_lines(test)
cleaned = cleanup_html(delined)
print(cleaned)
