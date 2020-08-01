from django.shortcuts import render, redirect, HttpResponseRedirect
from .models import Feed, Minwon, Life, FreeBoard, CoBuy, Rent, Keep, Resell, FeedComment, \
                    FeedLike, CommentLike, Recomment, RecommentLike, STAT_OPTION
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.paginator import Paginator 

from datetime import datetime, timedelta, date
from collections import OrderedDict

# 페이지 노출 시에 보여지는 게시판 이름들 정리
def get_board(board, category):
    board_info = ['', '', ''] 
    # 전체 리스트 게시판 항목 정보 1
    board_info[0] = '공통' if category.find('gong') != -1 else \
                    ('학부' if category.find('bachelor') != -1 else 
                    ('대학원' if category.find('master') != -1 else 
                    ('가족' if category.find('family') != -1 else 
                    ('BK' if category.find('bk') != -1 else ''))))

    # 전체 리스트 게시판 항목 정보 2
    board_info[1] = category.split('_')[1] + '동' if category.find('_') != -1 else \
                    ('공구' if category == 'cobuy' else 
                    ('대여' if category == 'rent' else 
                    ('보관' if category == 'keep' else 
                    ('중고' if category == 'resell' else ''))))
    
    # 게시판별 이름 정보  
    board_info[2] = '전체' if category == 'tori' else \
                    '공통' if category.find('gong') != -1 else board_info[1]

    return board_info

# 기본 PAGE
def showMain(request):
    if request.method == 'GET':
        today = datetime.now()
        today.strftime('%Y-%m-%d')
        tomorrow = datetime.now()-timedelta(days=1)
        tomorrow.strftime('%Y-%m-%d')
        week_ago = datetime.now()-timedelta(weeks=1)
        week_ago.strftime('%Y-%m-%d') 

        # 기숙사 각 동별 게시판 
        # dong = Minwon.objects.filter(category=request.user.profile.building_category, board=request.user.profile.building_dong) \
        #         if request.user.is_authenticated else Minwon.objects.filter(board_info1="학부", board_info2="906")
    
        dong = Minwon.objects.filter(board_info1="학부", board_info2="906동")

        # 전체게시판 = [ 주간게시글, 일간게시글 ] - 좋아요 기준 정렬
        gong_feeds = [ Minwon.objects.filter(category='gong', created_at__range=(week_ago, today)).order_by('-like_users')[:5],
                        Minwon.objects.filter(category='gong', created_at=today).order_by('-like_users')[:5] ]
        # 동별게시판 = [ 주간게시글, 일간게시글 ] - 좋아요 기준 정렬
        dong_feeds = [ dong.filter(created_at__range=(week_ago, today)).order_by('-like_users')[:5],
                        dong.filter(created_at=today).order_by('-like_users')[:5] ]
        # 생활게시판 - 시간 정렬
        life_feeds = [ [CoBuy.objects.all().order_by('-created_at')[:5], CoBuy.objects.all().order_by('-created_at')[5:10]],
                        [Keep.objects.all().order_by('-created_at')[:5], Keep.objects.all().order_by('-created_at')[5:10]],
                        [Rent.objects.all().order_by('-created_at')[:5], Rent.objects.all().order_by('-created_at')[5:10]],
                        [Resell.objects.all().order_by('-created_at')[:5], Resell.objects.all().order_by('-created_at')[5:10]]]
        # 자유게시판 - 좋아요 정렬
        free_feeds = FreeBoard.objects.all().order_by('-like_users')[:17]

        return render(request, 'feedpage/index.html', {'gong_feeds': gong_feeds, 'dong_feeds': dong_feeds,
                                'life_feeds': life_feeds,'free_feeds': free_feeds})

    elif request.method == 'POST':
        return redirect('/feeds')

# 게시판 list 보여주기
def showBoard(request, board, category):
    ''' ____________________________________________________________________
        |   board     |   category                       | list             
        |-------------|-----------------------------------------------------
        |  minwon     |  tori                            | 전체 게시판      
        |             |  gong                            | 생활관 공통      
        |             |  bachelor | master | family | bk | 생활관별 게시판  
        |             |  bachelor_906 etc                | 동별 게시판      
        |-------------|---------------------------------------------------- 
        |  life       |  tori                             | 전체 게시판      
        |             |  cobuy | rent | keep | resell     | 세부 기능 게시판 
        |-------------|-----------------------------------------------------
        |  freeboard  |  tori                             | 전체 게시판      
        ---------------------------------------------------------------------
    '''
    if request.method == 'GET':
        board_info = get_board(board, category)
        # 전체게시판 보여주기: minwon / life / freeboard
        if category == "tori":
            feeds = Minwon.objects.all() if board == "minwon" else \
                    (Life.objects.all() if board == "life" else
                    (FreeBoard.objects.all()))

        # 민원 게시판 보여주기
        elif board == "minwon":
            feeds = Minwon.objects.filter(board_info1=board_info[0], board_info2=board_info[1])

        # 생활 게시판 보여주기
        elif board == "life":
            feeds = CoBuy.objects.all() if category == "cobuy" else \
                    (Rent.objects.all() if category == "rent" else
                    (Keep.objects.all() if category == "keep" else
                    Resell.objects.all()))
        else:
            feeds = Feed.objects.all()
                
        # 전체글 버튼
        feeds = feeds.order_by('-created_at')
        paginator = Paginator(feeds, 1)
        page = request.GET.get('page')
        posts = paginator.get_page(page)

        # 베스트 버튼 
        best_feeds = feeds.order_by('-like_users')
        paginator2 = Paginator(best_feeds, 11)
        best_page = request.GET.get('best_page')
        best_posts = paginator2.get_page(best_page)

        return render(request, 'feedpage/show.html', {'posts':posts, 'best_posts': best_posts, 
                            'board': board, 'category': category, 'board_name': board_info[2]})

    elif request.method == 'POST':
        return redirect('showboard', board=board, category=category)


# Feed 생성
def newFeed(request, board, category):
    board_info = get_board(board, category)
    now_date = datetime.now()

    if request.method == 'GET':
        return render(request, 'feedpage/new.html', {'board': board, 'now_date': now_date,
                    'category': category, 'board_name': board_info[2] })

    elif request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']
        photo = request.POST['photo']
        noname = True if "noname" in request.POST else False
    
        # 민원 게시판 
        if board == "minwon":
            Minwon.objects.create(title=title, content=content, photo=photo, noname=noname, 
                                author=request.user, board=board, category=category,
                                board_info1=board_info[0], board_info2=board_info[1])
        # 자유 게시판 
        elif board == 'freeboard':
            FreeBoard.objects.create(title=title, content=content, photo=photo, noname=noname, 
                                    author=request.user, board=board, category=category,
                                    board_info1=board_info[0], board_info2=board_info[1])   
        # 생필품 게시판 
        elif board == "life":
            # cobuy 게시판 - (제목, 설명, 사진, 익명) + 가격, 링크, 마감일(+ 미정)
            if category == "cobuy":
                price = request.POST['price']
                url = request.POST['url']
                duedate = request.POST['duedate']
                CoBuy.objects.create(title=title, content=content, photo=photo, noname=noname,
                                    price=price, url=url, duedate=duedate, 
                                    author=request.user, board=board, category=category,
                                    board_info1=board_info[0], board_info2=board_info[1])

            # rent 게시판 - (제목, 설명, 사진, 익명) + 목적, 대여료, 시작일(+ 미정), 마감일(+ 미정)
            elif category == "rent":
                purpose = Rent.OPTION[0][0] if request.POST['purpose'] == 'borrow' else Rent.OPTION[1][0]
                deposit = request.POST['deposit']
                start_date = request.POST['start_date']
                end_date = request.POST['duedate']
                Rent.objects.create(title=title, content=content, photo=photo, noname=noname, deposit=deposit, 
                                    purpose=purpose, start_date=start_date, end_date=end_date, 
                                    author=request.user, board=board, category=category,
                                    board_info1=board_info[0], board_info2=board_info[1])

            # keep 게시판 - (제목, 설명, 사진, 익명) + 목적, 보관료, 시작일(+ 미정), 마감일(+ 미정)
            elif category == "keep":
                purpose = Keep.OPTION[0][0] if request.POST['purpose'] == 'keep' else Keep.OPTION[1][0]
                reward = request.POST['reward']
                start_date = request.POST['start_date']
                end_date = request.POST['duedate']
                Keep.objects.create(title=title, content=content, photo=photo, noname=noname, purpose=purpose, 
                                    reward=reward, start_date=start_date, end_date=end_date,
                                    author=request.user, board=board, category=category, 
                                    board_info1=board_info[0], board_info2=board_info[1])

            # resell 게시판 - (제목, 설명, 사진, 익명) + 목적, 가격
            elif category == "resell":
                purpose = Resell.OPTION[0][0] if request.POST['purpose'] == "sell" else Resell.OPTION[1][0]
                price = request.POST['price']
                Resell.objects.create(title=title, content=content, photo=photo, noname=noname, purpose=purpose, 
                                price=price, author=request.user, board=board, category=category,
                                board_info1=board_info[0], board_info2=board_info[1])

    return redirect('showboard', board=board, category=category)

# 특정 게시글 자세히 보기 
def showFeed(request, board, category, fid): # board, category 필요없음. 
    board_info = get_board(board, category)
    # 조회수 count 본인 게시글 조회 제외!
    feed = Feed.objects.filter(board=board, category=category, id=fid)

    if board == "minwon":
        feed = Minwon.objects.get(id=fid)

    elif board == "life":
        feed = CoBuy.objects.get(id=fid) if category == "cobuy" else \
            (Rent.objects.get(id=fid) if category == "rent" else 
            (Keep.objects.get(id=fid) if category == "keep" else 
            (Resell.objects.get(id=fid) if category == "resell" else "tori")))

    elif board == "freeboard":
        feed = FreeBoard.objects.get(id=fid)

    # if request.user.id != feed.author.id:
    #     feed.views += 1     
    #     feed.save()

    return render(request, 'feedpage/feed.html', {'feed': feed, 'board': board, 'fid':fid, 
                                        'category': category, 'board_name': board_info[2]})



# 게시글 수정
def editFeed(request, board, category, fid):
    board_info = get_board(board, category)
    if request.method == 'GET':
        complete = False

        if board == "minwon":
            feed = Minwon.objects.get(id=fid)

        elif board == "life":
            feed = CoBuy.objects.get(id=fid) if category == "cobuy" else \
                (Rent.objects.get(id=fid) if category == "rent" else 
                (Keep.objects.get(id=fid) if category == "keep" else 
                (Resell.objects.get(id=fid) if category == "resell" else "tori")))
            complete = True if feed.status == STAT_OPTION[2] else False

        elif board == "freeboard":
            feed = FreeBoard.objects.get(id=fid)

        return render(request, 'feedpage/edit.html', {'feed': feed, 'board': board, 'complete': complete,
                        'category': category, 'fid': fid, 'board_name': board_info[2] })

    elif request.method == 'POST':
        title = request.POST['title']
        content = request.POST['content']
        photo = request.POST['photo']
        noname = True if "noname" in request.POST else False
    
        # 민원 게시판 
        if board == "minwon":
            Minwon.objects.filter(id=fid).update(title=title, content=content, photo=photo, noname=noname, 
                                author=request.user, board=board, category=category,
                                board_info1=board_info[0], board_info2=board_info[1])
        # 자유 게시판 
        elif board == 'freeboard':
            FreeBoard.objects.filter(id=fid).update(title=title, content=content, photo=photo, noname=noname, 
                                    author=request.user, board=board, category=category,
                                    board_info1=board_info[0], board_info2=board_info[1])   

         # 생필품 게시판 
        elif board == "life":
            status = STAT_OPTION[0][0] if request.POST['status'] == '진행중' else \
                     (STAT_OPTION[1][0] if request.POST['status'] == '판매중' else (STAT_OPTION[2][0]))

            # cobuy 게시판 - (제목, 설명, 사진, 익명) + 가격, 링크, 마감일(+ 미정)
            if category == "cobuy":
                price = request.POST['price']
                url = request.POST['url']
                duedate = request.POST['duedate']
                CoBuy.objects.filter(id=fid).update(title=title, content=content, photo=photo, noname=noname,
                                            price=price, url=url, duedate=duedate, status=status,
                                            author=request.user, board=board, category=category)

            # rent 게시판 - (제목, 설명, 사진, 익명) + 목적, 대여료, 시작일(+ 미정), 마감일(+ 미정)
            elif category == "rent":
                deposit = request.POST['deposit']
                purpose = Rent.OPTION[0] if request.POST['purpose'] == 'borrow' else Rent.OPTION[1]
                start_date = request.POST['start_date']
                end_date = request.POST['duedate']
                Rent.objects.filter(id=fid).update(title=title, content=content, photo=photo, noname=noname, deposit=deposit, 
                                    purpose=purpose, start_date=start_date, end_date=end_date, 
                                    status=status, author=request.user, board=board, category=category)

            # keep 게시판 - (제목, 설명, 사진, 익명) + 목적, 보관료, 시작일(+ 미정), 마감일(+ 미정)
            elif category == "keep":
                purpose = Keep.OPTION[0] if request.POST['purpose'] == 'keep' else Keep.OPTION[1]
                reward = request.POST['reward']
                start_date = request.POST['start_date']
                end_date = request.POST['duedate']
                Keep.objects.filter(id=fid).update(title=title, content=content, photo=photo, noname=noname, purpose=purpose, 
                                    reward=reward, start_date=start_date, end_date=end_date, status=status, 
                                    author=request.user, board=board, category=category)

            # resell 게시판 - (제목, 설명, 사진, 익명) + 목적, 가격
            elif category == "resell":
                purpose = Resell.OPTION[0] if request.POST['purpose'] == 'sell' else Resell.OPTION[1]
                price = request.POST['price']
                Resell.objects.filter(id=fid).update(title=title, content=content, photo=photo, noname=noname, purpose=purpose, 
                                price=price, status=status, author=request.user, board=board, category=category)

    return redirect('showfeed', board=board, category=category, fid=fid)

# 게시글 삭제


def deleteFeed(request, board, category, fid):
    feed = Feed.objects.get(id=fid)
    feed.delete()

    return redirect('showboard', board=board, category=category)


# 민원게시판 게시글 좋아요
def likeFeed(request, board, category, fid):
    if request.method == 'GET':
        if board == "minwon":
            feed = Minwon.objects.get(id=fid)

        elif board == "life":
            feed = CoBuy.objects.get(id=fid) if category == "cobuy" else (Rent.objects.get(id=fid) if category == "rent" else (
            Keep.objects.get(id=fid) if category == "keep" else (Resell.objects.get(id=fid) if category == "resell" else "tori")))

        elif board == "freeboard":
            feed = FreeBoard.objects.get(id=fid)
        
        user_like = feed.feedlike.filter(user_id=request.user.id)
        if user_like.count() > 0:
            feed.feedlike.get(user_id=request.user.id).delete()
        else:
            FeedLike.objects.create(user_id=request.user.id, feed_id=feed.id)

    return render(request, 'feedpage/feed.html', {'feed': feed, 'board': board, 'category': category, 'fid': fid})


# 댓글 달기
def newComment(request, board, category, fid):
    content = request.POST['content']
    new_comment = FeedComment.objects.create(feed_id=fid, content=content, author = request.user)
    like_count = new_comment.commentlike_set.filter(user_id = request.user.id)
    noname = True if "noname" in request.POST else False

    context = {
        'cid': new_comment.id,
        'username': new_comment.author.username,
        'content': new_comment.content,
        'like_count': like_count.count(),
    }

    return JsonResponse(context)


def editComment(request, board, category, fid, cid):
    if request.method == 'POST':
        content = request.POST['content']
        FeedComment.objects.filter(id =cid).update(content = content)
        edit_comment = FeedComment.objects.get(id = cid)
        like_count = edit_comment.commentlike_set.filter(user_id = request.user.id)

        context = {
            'cid': edit_comment.id,
            'username': edit_comment.author.username,
            'content' : content,
        }

        return JsonResponse(context)




# 댓글 좋아요


def likeComment(request, board, category, fid, cid):
    feedcomment = FeedComment.objects.get(id=cid)
    like_list = feedcomment.commentlike_set.filter(user_id=request.user.id)
    if like_list.count() > 0:
        feedcomment.commentlike_set.get(user_id=request.user.id).delete()
    else:

        CommentLike.objects.create(user_id = request.user.id, comment_id = feedcomment.id)
    context = {
        'likecount': like_list.count()
    }
    return JsonResponse(context)
    # return redirect('showfeed', board=board, category=category, fid=fid)


# 댓글 삭제


def deleteComment(request, board, category, fid, cid):
    c = FeedComment.objects.get(id=cid)
    c.delete()
    return JsonResponse({})

# 대댓글 달기


def newRecomment(request, board, category, fid, cid):
    content = request.POST['content']
    new_recomment = Recomment.objects.create(
        comment_id=cid, content=content, author=request.user)
    like_count = new_recomment.recommentlike_set.filter(
        user_id=request.user.id)
    noname = True if "noname" in request.POST else False

    context = {
        'did': new_recomment.id,
        'username': new_recomment.author.username,
        'content': new_recomment.content,
        'like_count': like_count.count(),
    }

    return JsonResponse(context)

# 대댓글 수정 -- 미완성


def editRecomment(request, board, category, fid, cid):
    return redirect('showfeed', board=board, category=category, fid=fid)

# 대댓글 삭제


def deleteRecomment(request, board, category, fid, cid, rcid):
    c = Recomment.objects.get(id=rcid)
    c.delete()
    return JsonResponse({})


def likeRecomment(request, board, category, fid, cid, rcid):
    recomment = Recomment.objects.get(id=rcid)
    like_list = recomment.recommentlike_set.filter(user_id=request.user.id)
    if like_list.count() > 0:
        recomment.recommentlike_set.get(user_id=request.user.id).delete()
    else:
        RecommentLike.objects.create(user_id = request.user.id, recomment_id = recomment.id)
    
    context = {
        'likecount': like_list.count()
    }
    return JsonResponse(context)

def search(request):
    searchtype = request.GET
    query = request.GET['query']
    searchtype = request.GET['searchtype']
    feeds = Feed.objects.all()
    results = set()

    for feed in feeds:
        if searchtype == 'title':
            if feed.title.find(query) != -1:
                results.add(feed)
        elif searchtype == 'content':
            if feed.content.find(query) != -1:
                results.add(feed)
        elif searchtype == 'both':
            if feed.title.find(query) != -1:
                results.add(feed)
            elif feed.content.find(query) != -1:
                results.add(feed)
            
            

    return render(request, 'feedpage/search.html', {'results': results})

def searchmore(request, board, category):
    searchtype = request.GET
    query = request.GET['query']
    searchtype = request.GET['searchtype']
    feeds = Feed.objects.all()
    results = set()


    for feed in feeds:
        if searchtype == 'title':
            if feed.title.find(query) != -1:
                results.add(feed)
        elif searchtype == 'content':
            if feed.content.find(query) != -1:
                results.add(feed)
        elif searchtype == 'both':
            if feed.title.find(query) != -1:
                results.add(feed)
            elif feed.content.find(query) != -1:
                results.add(feed)

    return render(request, 'feedpage/search.html', {'results': results})
