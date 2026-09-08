function Code(element)
  local attributes = element.attributes
  attributes["custom-style"] = "Inline Code Emphasis"
  return pandoc.Span(
    { pandoc.Str(element.text) },
    pandoc.Attr(element.identifier, element.classes, attributes)
  )
end

local function has_class(element, target)
  for _, class_name in ipairs(element.classes) do
    if class_name == target then
      return true
    end
  end
  return false
end

local function literal_inlines(text)
  local inlines = pandoc.Inlines({})
  local position = 1
  local first_line = true

  while true do
    local newline = text:find("\n", position, true)
    local line = newline and text:sub(position, newline - 1) or text:sub(position)
    if not first_line then
      inlines:insert(pandoc.LineBreak())
    end
    if line ~= "" then
      inlines:insert(pandoc.Str(line))
    end
    if not newline then
      break
    end
    position = newline + 1
    first_line = false
  end

  return inlines
end

function CodeBlock(element)
  if not has_class(element, "text") then
    return nil
  end

  local block_attributes = {}
  for key, value in pairs(element.attributes) do
    block_attributes[key] = value
  end
  block_attributes["custom-style"] = "Source Code"

  local styled_text = pandoc.Span(
    literal_inlines(element.text),
    pandoc.Attr("", {}, { ["custom-style"] = "Text Code Block" })
  )
  return pandoc.Div(
    { pandoc.Para({ styled_text }) },
    pandoc.Attr(element.identifier, element.classes, block_attributes)
  )
end

local function styled_inlines(inlines, style_name)
  return pandoc.Inlines({
    pandoc.Span(inlines, pandoc.Attr("", {}, { ["custom-style"] = style_name }))
  })
end

local function styled_blocks(blocks, paragraph_style, text_style)
  -- Local character styles must also reach hyperlinks and inline-code spans.
  -- This walk only touches an explicitly marked author note or document metadata.
  local container = pandoc.Div(blocks):walk({
    Span = function(element)
      element.attributes["custom-style"] = nil
      return element
    end,
    Link = function(element)
      element.content = styled_inlines(element.content, text_style)
      return element
    end,
    Para = function(element)
      element.content = styled_inlines(element.content, text_style)
      return element
    end,
    Plain = function(element)
      element.content = styled_inlines(element.content, text_style)
      return element
    end,
  })
  container.attributes["custom-style"] = paragraph_style
  return container
end

function Para(element)
  if #element.content == 1 then
    local span = element.content[1]
    if span.t == "Span" and has_class(span, "doc-meta") then
      return styled_blocks({ pandoc.Para(span.content) }, "Doc Meta", "Doc Meta Text")
    end
  end
end

function BlockQuote(element)
  local first = element.content[1]
  if first and (first.t == "Para" or first.t == "Plain")
      and pandoc.utils.stringify(first) == "🔴 作者说明（供作者阅读，可整段删除）" then
    return styled_blocks(element.content, "Author Note", "Author Note Text")
  end
end
