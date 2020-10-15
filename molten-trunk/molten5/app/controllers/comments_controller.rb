class CommentsController < ProtectedController

  def create
    @comment = CaseComment.new(params[:comment].merge({:created_by_id => current_contact.id, :is_published => '1'}))
    unless @comment = @comment.save_and_clone
      logger.info("An error occurred add comment")
      return ajax_error("An error occurred saving the comment")
    end
  end
end
