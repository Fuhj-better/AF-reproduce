def process_line(line, in_block_comment):
    """
    处理单行代码，去除注释并返回有效代码部分及块注释状态。
    """
    effective = []
    i = 0
    n = len(line)
    while i < n:
        if in_block_comment:
            # 在块注释中，查找结束符*/
            if line[i] == '*' and i + 1 < n and line[i+1] == '/':
                in_block_comment = False
                i += 2  # 跳过*/两个字符
            else:
                i += 1
        else:
            # 不在块注释中，检查注释起始符
            if line[i] == '/' and i + 1 < n:
                if line[i+1] == '/':
                    # 单行注释，跳过剩余部分
                    break
                elif line[i+1] == '*':
                    # 进入块注释
                    in_block_comment = True
                    i += 2  # 跳过/*两个字符
                else:
                    # 普通/字符（如除法运算）
                    effective.append(line[i])
                    i += 1
            else:
                # 普通字符
                effective.append(line[i])
                i += 1
    # 拼接有效代码并去除行尾空白
    effective_line = ''.join(effective).rstrip()
    return effective_line, in_block_comment

def remove_comments(input_path, output_path):
    """
    读取输入文件，删除注释和空行，写入输出文件。
    """
    in_block_comment = False
    with open(input_path, 'r',encoding='utf-8') as infile, open(output_path, 'w',encoding='utf-8') as outfile:
        for line in infile:
            effective_line, in_block_comment = process_line(line, in_block_comment)
            if effective_line:
                outfile.write(effective_line + '\n')