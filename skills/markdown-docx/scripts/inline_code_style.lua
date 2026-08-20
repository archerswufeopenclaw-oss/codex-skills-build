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
