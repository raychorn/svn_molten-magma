module CommentsHelper
  def link_to_toggle_add_comment(name = "Cancel")
    link_to_function name, "Element.toggle('add_comment_form');",
    :id => "comments_button"
  end
  
  def tag_for_comments_list
    "comment_list"
  end
  
  def tag_for_comment(comment)
    "comment_#{comment.id}"
  end
  
  def comments_count(commentable)
    pluralize commentable.comments(true).size, "Comment"
  end
end
