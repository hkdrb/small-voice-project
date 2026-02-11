
import svgwrite

def create_er_diagram():
    dwg = svgwrite.Drawing('docs/images/er_diagram.svg', size=('1600px', '1600px'), profile='full')
    
    # colors
    c_user_bg = "#E1F5FE"
    c_user_stroke = "#01579B"
    c_survey_bg = "#E8F5E9"
    c_survey_stroke = "#2E7D32"
    c_analysis_bg = "#FFF3E0"
    c_analysis_stroke = "#EF6C00"
    c_casual_bg = "#F3E5F5"
    c_casual_stroke = "#7B1FA2"
    c_notif_bg = "#FFEBEE"
    c_notif_stroke = "#C62828"
    
    # Styles
    # Note: svgwrite doesn't support <style> easily in checking compatibility, using inline attributes or defs
    # We will use simple rects and texts
    
    def draw_table(x, y, title, pks=[], fks=[], width=260, height=None):
        if height is None:
             height = 40 + (len(pks) + len(fks)) * 16 + 10
        
        # Shadow/Drop
        # dwg.add(dwg.rect(insert=(x+2, y+2), size=(width, height), fill="#ccc", rx=4, ry=4))
        
        # Main box
        dwg.add(dwg.rect(insert=(x, y), size=(width, height), fill="#ffffff", stroke="#333", stroke_width=1, rx=4, ry=4))
        
        # Header
        dwg.add(dwg.text(title, insert=(x + width/2, y + 20), text_anchor="middle", font_family="monospace", font_weight="bold", font_size="14px", fill="#000"))
        
        # Line
        dwg.add(dwg.line(start=(x, y+30), end=(x+width, y+30), stroke="#ccc", stroke_width=1))
        
        # Fields
        curr_y = y + 48
        for pk in pks:
            dwg.add(dwg.text(f"PK {pk}", insert=(x + 10, curr_y), font_family="monospace", font_size="12px", fill="#333"))
            curr_y += 16
        for fk in fks:
            dwg.add(dwg.text(f"FK {fk}", insert=(x + 10, curr_y), font_family="monospace", font_size="12px", fill="#333"))
            curr_y += 16
            
        return (x, y, width, height)

    def draw_relation(start_rect, end_rect, start_side='bottom', end_side='top', dash=False):
        # Calculate start point
        sx, sy, sw, sh = start_rect
        ex, ey, ew, eh = end_rect
        
        if start_side == 'bottom':
            p1 = (sx + sw/2, sy + sh)
            d1 = (0, 20)
        elif start_side == 'top':
            p1 = (sx + sw/2, sy)
            d1 = (0, -20)
        elif start_side == 'left':
            p1 = (sx, sy + sh/2)
            d1 = (-20, 0)
        elif start_side == 'right':
            p1 = (sx + sw, sy + sh/2)
            d1 = (20, 0)
            
        if end_side == 'bottom':
            p2 = (ex + ew/2, ey + eh)
            d2 = (0, 20)
        elif end_side == 'top':
            p2 = (ex + ew/2, ey)
            d2 = (0, -20)
        elif end_side == 'left':
            p2 = (ex, ey + eh/2)
            d2 = (-20, 0)
        elif end_side == 'right':
            p2 = (ex + ew, ey + eh/2)
            d2 = (20, 0)

        # Basic path
        path = dwg.path(fill="none", stroke="#000", stroke_width=1.5)
        if dash:
            path.dasharray([5, 5])
            
        path.push('M', p1)
        path.push('l', d1) # Move out
        
        # Simple Manhattan routing logic
        # Move to mid x or mid y
        target = (p2[0] + d2[0], p2[1] + d2[1])
        curr = (p1[0] + d1[0], p1[1] + d1[1])
        
        # If going vertical primarily
        if start_side in ['top', 'bottom'] and end_side in ['top', 'bottom']:
            mid_y = (curr[1] + target[1]) / 2
            path.push('L', (curr[0], mid_y))
            path.push('L', (target[0], mid_y))
        
        # If going horizontal primarily
        elif start_side in ['left', 'right'] and end_side in ['left', 'right']:
            mid_x = (curr[0] + target[0]) / 2
            path.push('L', (mid_x, curr[1]))
            path.push('L', (mid_x, target[1]))
            
        # Mixed
        else:
             path.push('L', (target[0], curr[1])) # simple corner
        
        path.push('L', target)
        path.push('L', p2)
        
        # Marker
        path.set_markers((None, None, url_arrow))
        
        dwg.add(path)

    # Marker Def
    arrow = dwg.marker(id='arrow', insert=(10,3), size=(10,10), orient='auto')
    arrow.add(dwg.path(d='M0,0 L0,6 L9,3 z', fill='#000'))
    dwg.defs.add(arrow)
    url_arrow = "url(#arrow)"

    # --- DRAW GROUPS ---
    
    # Group 1: Center (User/Org)
    dwg.add(dwg.rect(insert=(600, 600), size=(600, 400), rx=10, ry=10, fill=c_user_bg, stroke=c_user_stroke, stroke_width=2, fill_opacity=0.2))
    dwg.add(dwg.text("User & Org Management", insert=(900, 630), text_anchor="middle", font_weight="bold", fill=c_user_stroke))
    
    # Group 2: Top (Survey)
    dwg.add(dwg.rect(insert=(600, 50), size=(600, 500), rx=10, ry=10, fill=c_survey_bg, stroke=c_survey_stroke, stroke_width=2, fill_opacity=0.2))
    dwg.add(dwg.text("Survey System", insert=(900, 80), text_anchor="middle", font_weight="bold", fill=c_survey_stroke))
    
    # Group 3: Right (Analysis)
    dwg.add(dwg.rect(insert=(1250, 400), size=(300, 900), rx=10, ry=10, fill=c_analysis_bg, stroke=c_analysis_stroke, stroke_width=2, fill_opacity=0.2))
    dwg.add(dwg.text("Analysis & Discussion", insert=(1400, 430), text_anchor="middle", font_weight="bold", fill=c_analysis_stroke))
    
    # Group 4: Bottom (Casual)
    dwg.add(dwg.rect(insert=(600, 1050), size=(600, 500), rx=10, ry=10, fill=c_casual_bg, stroke=c_casual_stroke, stroke_width=2, fill_opacity=0.2))
    dwg.add(dwg.text("Casual Board", insert=(900, 1080), text_anchor="middle", font_weight="bold", fill=c_casual_stroke))
    
    # Group 5: Left (Notifications)
    dwg.add(dwg.rect(insert=(100, 600), size=(400, 400), rx=10, ry=10, fill=c_notif_bg, stroke=c_notif_stroke, stroke_width=2, fill_opacity=0.2))
    dwg.add(dwg.text("Notifications", insert=(300, 630), text_anchor="middle", font_weight="bold", fill=c_notif_stroke))

    # --- DRAW TABLES ---
    
    # Center Group
    box_users = draw_table(630, 660, "users", ["id"], [], width=220)
    box_orgs = draw_table(950, 660, "organizations", ["id"], [], width=220)
    box_org_mem = draw_table(790, 800, "organization_members", ["id"], ["user_id", "org_id"], width=220)
    box_sessions = draw_table(630, 900, "sessions", ["id"], ["user_id"], width=220)

    # Top (Survey)
    box_surveys = draw_table(790, 400, "surveys", ["id"], ["org_id", "created_by"], width=220)
    box_questions = draw_table(790, 250, "questions", ["id"], ["survey_id"], width=220)
    box_answers = draw_table(650, 100, "answers", ["id"], ["sv_id", "q_id", "u_id"], width=200)
    box_surv_comm = draw_table(950, 100, "survey_comments", ["id"], ["sv_id", "u_id"], width=200)
    
    # Right (Analysis)
    box_ana_sess = draw_table(1290, 480, "analysis_sessions", ["id"], ["org_id"], width=220)
    box_ana_res = draw_table(1290, 600, "analysis_results", ["id"], ["session_id"], width=220)
    box_iss_def = draw_table(1290, 720, "issue_definitions", ["id"], ["session_id"], width=220)
    box_comments = draw_table(1290, 840, "comments", ["id"], ["sess_id", "u_id"], width=220)
    box_comm_likes = draw_table(1290, 980, "comment_likes", ["id"], ["comm_id", "u_id"], width=220)

    # Bottom (Casual)
    box_casual_posts = draw_table(790, 1100, "casual_posts", ["id"], ["org_id", "u_id"], width=220)
    box_casual_likes = draw_table(650, 1250, "casual_post_likes", ["id"], ["post_id", "u_id"], width=200)
    box_casual_ana = draw_table(950, 1250, "casual_analyses", ["id"], ["org_id"], width=200)

    # Left (Notifications)
    box_notif = draw_table(190, 750, "notifications", ["id"], ["u_id", "org_id"], width=220)
    
    # --- DRAW RELATIONS ---
    # Smart function needed to avoid overlaps. 
    # For now, manually specifying sides to ensure clean routing.

    # 1. Center Internal
    draw_relation(box_users, box_org_mem, 'bottom', 'left') # users -> org_mem
    draw_relation(box_orgs, box_org_mem, 'bottom', 'right') # orgs -> org_mem
    draw_relation(box_users, box_sessions, 'left', 'left') # users -> sessions

    # 2. To Survey (Top)
    draw_relation(box_orgs, box_surveys, 'top', 'bottom') # orgs -> surveys
    draw_relation(box_users, box_surveys, 'top', 'bottom', dash=True) # users -> surveys (created_by)
    
    draw_relation(box_surveys, box_questions, 'top', 'bottom') # surveys -> questions
    
    draw_relation(box_surveys, box_answers, 'left', 'bottom', dash=True) # surveys -> answers
    draw_relation(box_questions, box_answers, 'top', 'bottom') # questions -> answers
    draw_relation(box_users, box_answers, 'left', 'left', dash=True) # users -> answers -- LONG REACH! needs care.
    # Users is at (630, 660). Answers is at (650, 100).
    # Path: User Left -> Go Up -> Answers Left.
    
    draw_relation(box_surveys, box_surv_comm, 'right', 'bottom') # surveys -> survey_comments
    draw_relation(box_users, box_surv_comm, 'right', 'right', dash=True) # users -> survey_comments.
    # Users (850 is right edge of box). SurvComm (1150).
    # Path: User Right -> Go Up -> SurvComm Right.
    
    # 3. To Analysis (Right)
    draw_relation(box_orgs, box_ana_sess, 'right', 'left') # orgs -> ana_sess
    draw_relation(box_ana_sess, box_ana_res, 'bottom', 'top')
    draw_relation(box_ana_sess, box_iss_def, 'right', 'right') # wrap around
    draw_relation(box_ana_sess, box_comments, 'left', 'left') # wrap around left?
    
    draw_relation(box_users, box_comments, 'bottom', 'left', dash=True) # users -> comments
    draw_relation(box_comments, box_comm_likes, 'bottom', 'top')
    draw_relation(box_users, box_comm_likes, 'bottom', 'left', dash=True) # users -> comment_likes

    # 4. To Casual (Bottom)
    draw_relation(box_orgs, box_casual_posts, 'bottom', 'top') # orgs -> casual
    draw_relation(box_users, box_casual_posts, 'bottom', 'top', dash=True) # users -> casual
    
    draw_relation(box_casual_posts, box_casual_likes, 'left', 'top')
    draw_relation(box_users, box_casual_likes, 'left', 'left', dash=True) # users -> casual_likes
    
    draw_relation(box_orgs, box_casual_ana, 'bottom', 'top', dash=True) # orgs -> casual_ana (Long reach)
    
    # 5. To Notifications (Left)
    draw_relation(box_users, box_notif, 'left', 'right')
    draw_relation(box_orgs, box_notif, 'top', 'top', dash=True) # orgs -> notif (Around top of Users?)
    
    dwg.save()

if __name__ == '__main__':
    create_er_diagram()
