class TopicsController < AbstractBeastController
  prepend_before_filter :find_forum_and_topic, :except => [:index, :active]
#  before_filter :update_last_seen_at, :only => :show

  def index
    respond_to do |format|
      format.html { redirect_to forum_path(params[:forum_id]) }
      format.xml do
        @topics = Topic.find_all_by_forum_id(params[:forum_id], :order => 'sticky desc, replied_at desc', :limit => 25)
        render :xml => @topics.to_xml
      end
    end
  end
  
  # Retrieves a list of the most active, unabused topics
  def active
    options = {}
    options[:per_page]   = 25
    options[:select]     = "topic.*, (SELECT COUNT(*) from post WHERE post.topic_id = topic.id AND #{Post.abusive_post_conditions} ) AS posts_count"
    options[:joins]      = 'inner join forum on topic.forum_id = forum.id'
    options[:order]      = 'posts_count desc, replied_at DESC'
    options[:conditions] = Topic.abusive_topic_conditions
    
    @topic_pages, @topics = paginate(:topic, options)
    @users = Sfcontact.find(:all, :select => 'distinct *', :conditions => ['sf_id in (?)', @topics.map { |t| t.posts.first }.collect(&:user_id).uniq]).index_by(&:id)
  end

  def new
    @topic = Topic.new
  end
  
  def show
    respond_to do |format|
      format.html do
        # see notes in application.rb on how this works
        update_last_seen_at
        # keep track of when we last viewed this topic for activity indicators
        (session[:topics] ||= {})[@topic.id] = Time.now.utc 
        # authors of topics don't get counted towards total hits
        @topic.hit! unless @topic.user == current_contact
        @post_pages, @posts = paginate(:posts, :per_page => 25, :order => 'post.created_at', :conditions => ["post.topic_id = ? AND #{@topic.class.abusive_post_conditions}", params[:id]])
        @post   = Post.new
      end
      format.xml do
        render :xml => @topic.to_xml
      end
      format.rss do
        @posts = @topic.posts.find(:all, :order => 'created_at desc', :limit => 25)
        render :action => 'show.rxml', :layout => false
      end
    end
  end
  
  def create
    # this is icky - move the topic/first post workings into the topic model?
    Topic.transaction do
      @topic  = @forum.topics.build(params[:topic])
      assign_protected
      @post   = @topic.posts.build(params[:topic])
      @post.topic=@topic
      @post.user = current_contact
      
      # only save topic if post is valid so in the view topic will be a new record if there was an error
      @topic.body = @post.body # incase save fails and we go back to the form
      @topic.save! if @post.valid?
      @post.save! 
    end
    respond_to do |format|
      format.html { redirect_to topic_path(@forum, @topic) }
      format.xml  { head :created, :location => formatted_topic_url(:forum_id => @forum, :id => @topic, :format => :xml) }
    end
  end
  
  def update
    @topic.attributes = params[:topic]
    assign_protected
    @topic.save!
    respond_to do |format|
      format.html { redirect_to topic_path(@forum, @topic) }
      format.xml  { head 200 }
    end
  end
  
  def destroy
    @topic.destroy
    flash[:notice] = "Topic '{title}' was deleted."[:topic_deleted_message, CGI::escapeHTML(@topic.title)]
    respond_to do |format|
      format.html { redirect_to forum_path(@forum) }
      format.xml  { head 200 }
    end
  end
  
  protected
    def assign_protected
      @topic.user     = current_contact if @topic.new_record?
      # admins and moderators can sticky and lock topics
      return unless current_contact.forum_admin? or current_contact.moderator_of?(@topic.forum)
      @topic.sticky, @topic.locked = params[:topic][:sticky], params[:topic][:locked] 
      # only admins can move
      return unless current_contact.forum_admin?
      @topic.forum_id = params[:topic][:forum_id] if params[:topic][:forum_id]
    end
    
    def find_forum_and_topic
      @forum = Forum.find(params[:forum_id])
      @topic = Topic.find(params[:id]) if params[:id]
    end
    
    def authorized?
      %w(new create active).include?(action_name) || @topic.editable_by?(current_contact)
    end
end
