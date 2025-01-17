# -*- encoding = gb18030 -*-
import codecs
from abc import ABCMeta, abstractmethod
from scipy.stats.stats import pearsonr

from deep.util.parameter_operation import save_params_val 
import deep.util.config as config 

from deep.manage.algorithm import beam_search, greed,beam_search_t
from deep.util.idf import get_idf
#from deep.util.sense.judge_make_sense import isMakeSense
from deep.util.various_strings import variousen_strings
import numpy as np
import time
import os
# from seg.Global import SegProcess



class ModelManager :
    __metaclass__ = ABCMeta
   
    def __init__(self):
        """
        Different init in sub class. 
        """
    
    
    def train(self):
        """
        Train a model.
        """
        if self.conf_dict['shuffle'] :
            self.cr.shuffle()  # The data may be shuffle by some implement of CorpusReader, but NOT ALL.
        n_train_set, n_valid_set, n_test_set = self.cr.get_size()
        n_batches = (n_train_set - 1) / self.conf_dict['batch_size'] + 1
        n_test_batches=(n_test_set - 1) / self.conf_dict['batch_size'] + 1 
        train_model = self.model.get_training_function(self.cr, batch_size=self.conf_dict['batch_size'],
                                                       batch_repeat=1)
        print ('train_model_data')
        #valid_model = self.model.get_validing_function(self.cr)
        test_model, pr_model = self.model.get_testing_function(self.cr,batch_size=self.conf_dict['batch_size'])
        
        print ('Start to train.') 
        epoch = 0
        if n_batches>200:
            n_epochs = 1
        else:
            n_epochs = 1
        it = 0
        test_errors=[]
        min_error=1000000
        min_error_index=0
        while (epoch < n_epochs):
            epoch += 1
            for i in xrange(n_batches):
                # train model
                train_error = train_model(i)[0]
                it = it + 1
                if(it % self.conf_dict['save_freq'] == 0):
                    '''
                    valid_error = valid_model()[0]
                    # valid model
                    print ('@iter: %s\tTraining Error: %s\tValid Error: %s.' % 
                                 (it, str(train_error), str(valid_error)))
                    '''
                    print ('@iter: %s\tTraining Error: %s' % 
                                 (it, str(train_error)))
                    # Save model parameters
                    #print ('Saving parameters to %s.' % (self.param_path))
                    #save_params_val(self.param_path, self.model.get_parameters())
            # test model
            print str(epoch)
            #save_params_val(self.param_path + str(epoch), self.model.get_parameters())
            #test_error=test_model()
            test_error=0
            for test_model_i in xrange(n_test_batches):
                test_error += test_model(test_model_i)[0]
            test_error/=n_test_batches
            print ('Now testing model. Test Error: %s' % (str(test_error)))
            if(len(test_errors)>2 and test_error > max(test_errors[-3:])):
                pass
                #self.model.options["learning_rate"]=self.model.options["learning_rate"]/2
            test_errors.append(test_error)
            if(test_error<min_error):
                min_error=test_error
                min_error_index=epoch
                final_parameter=self.model.get_parameters()
                save_params_val(self.param_path,final_parameter)
            final_parameter=self.model.get_parameters()
            save_params_val(self.param_path,final_parameter)
        final_path=self.param_path+str(min_error_index)
        #save_params_val(self.param_path,final_parameter)
        print final_path

            
    def generate(self, input_file, output_file):
        """
        Generate a model.
        """
        deploy_model = self.model.get_deploy_function()
        with open(output_file, 'w') as fw:
            with codecs.open(input_file, 'r', config.globalCharSet()) as fo:
                for line in fo.readlines() :
                    # line_word, line_zi = SegProcess(line.strip())
                    # line = line_zi.decode("gb18030")
                    line = line.strip()
                    print (line.encode(config.globalCharSet()))
                    fw.writelines('%s\n' % line.encode(config.globalCharSet()))
                    res, score = beam_search(line, self.cr, deploy_model, beam_size=200, search_scope=200)
                    print res
                    res = [' '.join(self.cr.transform_input_text(s)) for s in res]
                    for r, s in zip(res, score) :

                        print ('result: %s, score: %f.' % (r, s))
                        fw.writelines('result: %s, score: %f.\n' % (r, s))


    def generate_b_v(self, input_file, output_file):
        """
        Generate a model with special optimizers.
        """
        deploy_model = self.model.get_deploy_function()
        with codecs.open(output_file, 'w', config.globalCharSet()) as fw:
            with codecs.open(input_file, 'r', config.globalCharSet()) as fo:
                for line in fo.readlines() :
                    # line_word, line_zi = SegProcess(line.strip())
                    # line = line_word.decode("gb18030")
                    # line = line_word
                    line = line.strip()
                    #question_make_sense = isMakeSense(line)
                    question_make_sense=1
                    print (line.encode(config.globalCharSet()))
                    fw.writelines('%s\n' % line)
                    res, score = beam_search(line, self.cr, deploy_model, beam_size=1000, search_scope=1000)
                    print res
                    res = [' '.join(self.cr.transform_input_text(s)) for s in res]
                    resorted_list = list()
                    for r, s in zip(res, score):
                        idf = 0.0
                        tokens = r.split(u' ')
                        for token in tokens[1:-1]:
                            idf += get_idf(token)
            #                         idf /= len(tokens)
            #                         idf_revise = 1 / (1 +  np.exp(-2 / idf))
                        idf_revise = 4 * np.tanh(4 * idf)
                        resorted_list.append((r, s, s))
                    if len(line) > 3:
                        resorted_list = sorted(resorted_list, key=lambda x:x[2] / len(line) ** 1)
                    else:
                        resorted_list = sorted(resorted_list, key=lambda x:x[2])

                    candidates = list()

                    if question_make_sense == 1:
                        f = 0
                        for r, _, _ in resorted_list[:5]:
                            ori_sentence = r.replace(u'<END>', u'').replace(u' ', u'')
                            #if isMakeSense(ori_sentence) == 1:
                            if 1:
                                f += 1
                        if f <= 1:
                            question_make_sense = 0

                    for r, s1, s2 in resorted_list:
                        ori_sentence = r.strip().replace(u'<END>', u'')
                        ori_sentence = ori_sentence.replace(u' ', u'')
                        answer_make_sense = 1 #isMakeSense(ori_sentence)
                        r0 = r
                        if isinstance(r, unicode) :
                            r0 = r.encode(config.globalCharSet())
                        print r0, s1, s2, answer_make_sense,

                        if len(ori_sentence) <= 3 \
                            and len(ori_sentence) < len(line) and ori_sentence in line:
                            print 'continue1'
                            continue

                        if answer_make_sense == -1:
                            print 'continue2'
                            continue

                        if question_make_sense == 1 and answer_make_sense <= 0:
                            print 'continue3'
                            continue

                #             r_token_count = len(ori_sentence.strip().split(u' '))
                #             if question_word_count > 1 and r_token_count == 1:
                #                 print 'continue4'
                #                 continue
                        candidates.append((r, s2))

                    print 'variousen'

                    variousen_scope = 15
                    output_size = 5
                    high_fruq_left = 4
                    v_index = variousen_strings(candidates[:variousen_scope], output_size)
                    v_index = range(min(len(candidates), high_fruq_left)) + v_index
                #                     print v_index
                    func = lambda x, y:x if y in x else x + [y]
                    v_index = reduce(func, [[], ] + v_index)

                    toReturn = [candidates[i] for i in v_index[:output_size]]
                    for r, s in toReturn :
                        print ('result: %s, score: %f.' % (r.encode(config.globalCharSet()), s))
                        fw.writelines('result: %s, score: %f.\n' % (r, s))
    def generate_b_v_t(self, input_file, output_file):
        """
        Generate a model with special optimizers.
        """
        answer_set=[]
        answer_dict={}
        for answer_smaple in answer_set:
            tmp=[]
            for i in range(len(answer_smaple)):
                tmp.append(answer_smaple[i])
                #print map(str,tmp)
                answer_dict[str(tmp)]=1
        deploy_model = self.model.get_deploy_function()
        print output_file
        start = time.clock()
        with codecs.open(output_file, 'w', config.globalCharSet()) as fw:
            with codecs.open(input_file, 'r', config.globalCharSet()) as fo:
                for line in fo.readlines() :
                    # line_word, line_zi = SegProcess(line.strip())
                    # line = line_word.decode("gb18030")
                    # line = line_word
                    line = line.strip()
                    lines=line.split('\t')
                    line1=lines[0]+'\t'+lines[2]+'\t'+lines[3]+'\n'
                    question_make_sense = 1#isMakeSense(line)
                    #print (line.encode(config.globalCharSet()))
                    #fw.writelines('%s\n' % line)
                    #line=lines[0]+'\t1\n'
                    res, score = beam_search_t(line1, self.cr, deploy_model,answer_dict, beam_size=10, search_scope=10)
                    #print score
                    if(len(res)<=0):
                        print 'not find'
                        continue
                    for i in range(1):
                        res1=[res[i][1:-1]]
                    #print res,score
                        res1 = [' '.join(self.cr.transform_input_text(s)) for s in res1]
                        try:
                            fw.write(line+'\t'+res1[0]+'\t'+str(score[i])+'\n')
                            #fw.write(line+'\n')
                        except:
                            print res
                    '''
                    resorted_list = list()
                    for r, s in zip(res, score):
                        idf = 0.0
                        tokens = r.split(u' ')
                        for token in tokens[1:-1]:
                            idf += get_idf(token)
                #                         idf /= len(tokens)
                #                         idf_revise = 1 / (1 +  np.exp(-2 / idf))
                        idf_revise = 4 * np.tanh(4 * idf)
                        resorted_list.append((r, s, s))
                    if len(line) > 3:
                        resorted_list = sorted(resorted_list, key=lambda x:x[2] / len(line) ** 1)
                    else:
                        resorted_list = sorted(resorted_list, key=lambda x:x[2])

                    candidates = list()

                    if question_make_sense == 1:
                        f = 0
                        for r, _, _ in resorted_list[:5]:
                            ori_sentence = r.replace(u'<END>', u'').replace(u' ', u'')
                            #if isMakeSense(ori_sentence) == 1:
                            if 1:
                                f += 1
                        if f <= 1:
                            question_make_sense = 0

                    for r, s1, s2 in resorted_list:
                        ori_sentence = r.strip().replace(u'<END>', u'')
                        ori_sentence = ori_sentence.replace(u' ', u'')
                        answer_make_sense = 1#isMakeSense(ori_sentence)
                        r0 = r
                        if isinstance(r, unicode) :
                            r0 = r.encode(config.globalCharSet())
                        print r0, s1, s2, answer_make_sense,

                        if len(ori_sentence) <= 3 \
                            and len(ori_sentence) < len(line) and ori_sentence in line:
                            print 'continue1'
                            continue

                        if answer_make_sense == -1:
                            print 'continue2'
                            continue

                        if question_make_sense == 1 and answer_make_sense <= 0:
                            print 'continue3'
                            continue

                #             r_token_count = len(ori_sentence.strip().split(u' '))
                #             if question_word_count > 1 and r_token_count == 1:
                #                 print 'continue4'
                #                 continue
                        candidates.append((r, s2))

                    print 'variousen'

                    variousen_scope = 15
                    output_size = 5
                    high_fruq_left = 4

                    v_index = variousen_strings(candidates[:variousen_scope], output_size)
                    v_index = range(min(len(candidates), high_fruq_left)) + v_index
            #                     print v_index
                    func = lambda x, y:x if y in x else x + [y]
                    v_index = reduce(func, [[], ] + v_index)

                    toReturn = [candidates[i] for i in v_index[:output_size]]
                    for r, s in toReturn :
                        print ('result: %s, score: %f.' % (r.encode(config.globalCharSet()), s))
                        fw.writelines('result: %s, score: %f.\n' % (r, s))

                    for r in res[0:5] :
                        #fw.writelines('result: %s, score: %f\n' % (r.encode(config.globalCharSet()), s))
                        fw.writelines('result: %s, score: %f\n' % (r, s))
                    fw.writelines('\n')
                    '''
        end = time.clock()
        print "read: %f s" % (end - start)
    def generate_b_v_t_g(self, input_file, output_file):
        """
        Generate a model with special optimizers.
        """
        deploy_model = self.model.get_deploy_function()
        #get_cost= self.model.get_cost()
        print output_file
        print 'generate_b_v_t_g'
        with codecs.open(output_file, 'w', config.globalCharSet()) as fw:
            with codecs.open(input_file, 'r', config.globalCharSet()) as fo:
                for line in fo.readlines() :
                    # line_word, line_zi = SegProcess(line.strip())
                    # line = line_word.decode("gb18030")
                    # line = line_word
                    line = line.strip()
                    lines = line.strip().split('\t')
                    #(question, question_mask) = self.cr.transform_input_data(lines[0])
                    #(answer, answer_mask) = self.cr.transform_input_data(lines[1])
                    #qa_cost=get_cost(question, question_mask,answer,answer_mask,[[string.atoi(lines[2])]])
                    #fw.write(line+'\t'+str(qa_cost)+'\n')
                    
                    question_make_sense = 1#isMakeSense(line)
                    print (line.encode(config.globalCharSet()))
                    #fw.writelines('%s\n' % line)
                    if(len(lines)==3):
                        line=''
                        line+=lines[0]
                        line+='\t'
                        line+=lines[2]
                    fw.writelines('%s\n' % line)
                    res, score = beam_search_t(line, self.cr, deploy_model, beam_size=200, search_scope=100)
                    print res
                    res1= [s[:-1] for s in res]
                    res2= [s[-1] for s in res]
                    res = [' '.join(self.cr.transform_input_text(s)) for s in res1]
                    for res_len in range(len(res)):
                        res[res_len]+='\t'
                        res[res_len]+=str(res2[res_len])

                    resorted_list = list()
                    for r, s in zip(res, score):
                        idf = 0.0
                        tokens = r.split(u' ')
                        for token in tokens[1:-1]:
                            idf += get_idf(token)
                #                         idf /= len(tokens)
                #                         idf_revise = 1 / (1 +  np.exp(-2 / idf))
                        idf_revise = 4 * np.tanh(4 * idf)
                        resorted_list.append((r, s, s))
                    if len(line) > 3:
                        resorted_list = sorted(resorted_list, key=lambda x:x[2] / len(line) ** 1)
                    else:
                        resorted_list = sorted(resorted_list, key=lambda x:x[2])

                    candidates = list()

                    if question_make_sense == 1:
                        f = 0
                        for r, _, _ in resorted_list[:5]:
                            ori_sentence = r.replace(u'<END>', u'').replace(u' ', u'')
                            #if isMakeSense(ori_sentence) == 1:
                            if 1:
                                f += 1
                        if f <= 1:
                            question_make_sense = 0

                    for r, s1, s2 in resorted_list:
                        ori_sentence = r.strip().replace(u'<END>', u'')
                        ori_sentence = ori_sentence.replace(u' ', u'')
                        answer_make_sense = 1#isMakeSense(ori_sentence)
                        r0 = r
                        if isinstance(r, unicode) :
                            r0 = r.encode(config.globalCharSet())
                        print r0, s1, s2, answer_make_sense

                        if len(ori_sentence) <= 3 \
                            and len(ori_sentence) < len(line) and ori_sentence in line:
                            print 'continue1'
                            continue

                        if answer_make_sense == -1:
                            print 'continue2'
                            continue

                        if question_make_sense == 1 and answer_make_sense <= 0:
                            print 'continue3'
                            continue

                #             r_token_count = len(ori_sentence.strip().split(u' '))
                #             if question_word_count > 1 and r_token_count == 1:
                #                 print 'continue4'
                #                 continue
                        candidates.append((r, s2))

                    print 'variousen'

                    variousen_scope = 15
                    output_size = 5
                    high_fruq_left = 5

                    v_index = variousen_strings(candidates[:variousen_scope], output_size)
                    v_index = range(min(len(candidates), high_fruq_left)) + v_index
            #                     print v_index
                    func = lambda x, y:x if y in x else x + [y]
                    v_index = reduce(func, [[], ] + v_index)

                    toReturn = [candidates[i] for i in v_index[:output_size]]
                    for r, s in toReturn :
                        print ('result: %s, score: %f.' % (r.encode(config.globalCharSet()), s))
                        fw.writelines('result: %s, score: %f.\n' % (r, s))
                    '''
                    for r in res[0:5] :
                        #fw.writelines('result: %s, score: %f\n' % (r.encode(config.globalCharSet()), s))
                        fw.writelines('result: %s, score: %f\n' % (r, s))
                    #fw.writelines('\n')
                    '''
    def generate_b_v_t_v(self, input_file, output_file):
        #print output_file
        #print 'generate_b_v_t_g'
        get_cost= self.model.get_cost()
        with codecs.open(output_file, 'w', config.globalCharSet()) as fw:
            with codecs.open(input_file, 'r', config.globalCharSet()) as fo:
                for line in fo.readlines() :
                    line = line.strip()
                    lines = line.strip().split('\t')
                    (question, question_mask) = self.cr.transform_input_data(lines[-2])
                    #(answer, answer_mask) = self.cr.transform_input_data(lines[1])
                    #(context,context_mask,context_mask2)=self.cr.transform_input_data_context(lines[3:])
                    #print question, question_mask
                    #print answer, answer_mask
                    #print lines[1]
                    qa_cost=get_cost(question, question_mask)
                    fw.write(line.strip()+'\t'+str(qa_cost)+'\n')
    def generate_emb(self, input_file, output_file):
        #print output_file
        #print 'generate_b_v_t_g'
        get_cost= self.model.get_encoder_vector()
        with codecs.open(output_file, 'w', config.globalCharSet()) as fw:
            with codecs.open(input_file, 'r', config.globalCharSet()) as fo:
                for line in fo.readlines() :
                    line = line.strip()
                    lines = line.strip().split('\t')
                    (question, question_mask) = self.cr.transform_input_data(lines[0])
                    #(answer, answer_mask) = self.cr.transform_input_data(lines[1])
                    #(context,context_mask,context_mask2)=self.cr.transform_input_data_context(lines[3:])
                    #print question, question_mask
                    #print answer, answer_mask
                    #print lines[1]
                    qa_cost=get_cost(question, question_mask)
                    fw.write(line.strip()+'\t'+' '.join(str(i) for i in qa_cost[0])+'\n')
