module AttachmentsHelper
  def link_to_toggle_attach_file(name = "Cancel")
    link_to_function name, "Element.toggle('upload_form');", :id => "attachments_button"
  end
end
