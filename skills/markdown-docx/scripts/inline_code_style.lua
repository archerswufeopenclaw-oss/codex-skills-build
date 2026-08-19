function Code(element)
  local attributes = element.attributes
  attributes["custom-style"] = "Inline Code Emphasis"
  return pandoc.Span(
    { pandoc.Str(element.text) },
    pandoc.Attr(element.identifier, element.classes, attributes)
  )
end
