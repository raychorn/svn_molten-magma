class Admin::ArticlesController < AbstractAdminController
  before_filter :set_article, :only => [:edit, :update, :destroy]
  
  def list
    @articles = Article.find(:all, :order => "created_at DESC")
    render(:action => 'list')
  end
  alias index list
  
  def edit
    
  end
  
  def update
    if @article.update_attributes(params[:article])
      flash[:notice] = "Article updated successfully."
      return redirect_to(:action => 'list')
    else
      return render(:action => 'edit')
    end
  end
  
  def create
    @article = Article.new(params[:article])
    if @article.save
      flash[:notice] = "Article created."
      return redirect_to(:action => 'list')
    else
      return render(:action => 'new')
    end
  end
  
  def destroy
    @article.destroy
    flash[:notice] = "Article destroyed."
    redirect_to(:action => 'list')
  end
  
  private
  
  def set_article
    @article = Article.find(params[:id])
  end
end
