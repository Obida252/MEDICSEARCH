PGDMP  )    #                 }            medications_db    17.2    17.2     	           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            
           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false                       0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false                       1262    16435    medications_db    DATABASE     �   CREATE DATABASE medications_db WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'English_United States.1252';
    DROP DATABASE medications_db;
                     postgres    false            �            1259    16570    subforms    TABLE     �   CREATE TABLE public.subforms (
    subform_id integer NOT NULL,
    subform_name character varying(255),
    form_id integer
);
    DROP TABLE public.subforms;
       public         heap r       postgres    false            �            1259    16569    subforms_subform_id_seq    SEQUENCE     �   CREATE SEQUENCE public.subforms_subform_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 .   DROP SEQUENCE public.subforms_subform_id_seq;
       public               postgres    false    226                       0    0    subforms_subform_id_seq    SEQUENCE OWNED BY     S   ALTER SEQUENCE public.subforms_subform_id_seq OWNED BY public.subforms.subform_id;
          public               postgres    false    225            n           2604    16573    subforms subform_id    DEFAULT     z   ALTER TABLE ONLY public.subforms ALTER COLUMN subform_id SET DEFAULT nextval('public.subforms_subform_id_seq'::regclass);
 B   ALTER TABLE public.subforms ALTER COLUMN subform_id DROP DEFAULT;
       public               postgres    false    225    226    226                      0    16570    subforms 
   TABLE DATA           E   COPY public.subforms (subform_id, subform_name, form_id) FROM stdin;
    public               postgres    false    226   .                  0    0    subforms_subform_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.subforms_subform_id_seq', 2158, true);
          public               postgres    false    225            p           2606    16575    subforms subforms_pkey 
   CONSTRAINT     \   ALTER TABLE ONLY public.subforms
    ADD CONSTRAINT subforms_pkey PRIMARY KEY (subform_id);
 @   ALTER TABLE ONLY public.subforms DROP CONSTRAINT subforms_pkey;
       public                 postgres    false    226            r           2606    16577 "   subforms subforms_subform_name_key 
   CONSTRAINT     e   ALTER TABLE ONLY public.subforms
    ADD CONSTRAINT subforms_subform_name_key UNIQUE (subform_name);
 L   ALTER TABLE ONLY public.subforms DROP CONSTRAINT subforms_subform_name_key;
       public                 postgres    false    226            s           2606    16578    subforms subforms_form_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.subforms
    ADD CONSTRAINT subforms_form_id_fkey FOREIGN KEY (form_id) REFERENCES public.pharmaceutic_form(form_id);
 H   ALTER TABLE ONLY public.subforms DROP CONSTRAINT subforms_form_id_fkey;
       public               postgres    false    226               o  x��WKr�6]���2��� H��Y��HHF
�@��ۤ��ϡ���mP9���l	�}���E�v�'���[6I�U���-!)�|�OET,���V��	���{ʒit���1����8dj�S�3
}��4gg�%�)mu�U���H.�7�U��:�H����I+&�Y?j����ғg^��`ƓO�71G�o�x=Ա?~݊���4Wi[9�`�*#�d��3���K4f�� �a�u�)@�Y�ֿJk�Q��R$�������jEΤ��)�fU3�?`!�	j��ӺY�v�	����>���$��I���wk�N|���F�h�ьA��/�trW�"�gE�"�C7Z���� 6*�|����`��P��� &��`k�F��eJ�<� T���>�W�Dy���Rߡ��,�E8^@͌h(n�}hQ���X�Lt/�x~+�RZ��'��jR���!�<n��~�h�ۿ=F���-�ꔆb>��ux�V���`s	��B� &4��CX��E5HH�S�)���Wq)?��ǆVË��t�� ����Jx�cS��`�a�^���W@HY�fP��ð�Ƈ���S����d�fA��|D���m$_{�(��w��m�&i5ꛒeN���_�"Ftj���h%��u�@,J�GL��rhe�{6����. Z=��<NCƲ��pqB���I�2㴉g�p/Y�ʨk�T �4�^�Y9�~����4� ^���M%��4�,���s���*\$�*�bĊ�\�.9TE|g��b����JcA?a���=�0v����%L����� ��>ʊ���e���I\*�:�=ߪ��b�`�1��=<j���!�F
�����Ƭ���gu�1����d�,/�6pk]F7ϰ�y�T,@y��q��u��&!x[4�� ��k�E-�u˓��,�d��ꮡ��?�:%B�|%����r ���X�o��jo5|u!
�B�3*��A��esV\$�E���ޛ��4��z��Y�!�8�%����jC���~j�cO�<4޲v1wƪ/��˗���c?VXSo�P��<-J���g��I�� �M��&eM���?��F���U��/��ڀ��?f���1M�� (W^�     